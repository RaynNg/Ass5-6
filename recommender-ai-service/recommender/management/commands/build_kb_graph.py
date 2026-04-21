"""
Management command: python manage.py build_kb_graph

Reads data_user500.csv and builds a Neo4j knowledge-base graph:

Nodes:
  (:User  {id})
  (:Product {id})

Direct relationships (one per CSV row):
  (User)-[:VIEWED        {timestamp}]->(Product)
  (User)-[:CLICKED       {timestamp}]->(Product)
  (User)-[:ADDED_TO_CART {timestamp}]->(Product)

Derived relationships (aggregated):
  (Product)-[:CO_PURCHASED_WITH {count}]->(Product)
  (Product)-[:CO_VIEWED_WITH    {count}]->(Product)
"""

import csv, os
from django.core.management.base import BaseCommand
from neo4j import GraphDatabase

NEO4J_URI      = os.environ.get("NEO4J_URI",      "bolt://neo4j:7687")
NEO4J_USER     = os.environ.get("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "bookstore123")

CSV_CANDIDATES = [
    "/app/data_user500.csv",
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data_user500.csv"),
]

ACTION_TO_REL = {
    "view":         "VIEWED",
    "click":        "CLICKED",
    "add_to_cart":  "ADDED_TO_CART",
}


class Command(BaseCommand):
    help = "Build Neo4j Knowledge Base Graph from data_user500.csv"

    def handle(self, *args, **options):
        csv_path = next((p for p in CSV_CANDIDATES if os.path.exists(p)), None)
        if not csv_path:
            self.stderr.write("data_user500.csv not found")
            return

        self.stdout.write(f"Using: {csv_path}")
        self.stdout.write("Connecting to Neo4j…")

        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        try:
            driver.verify_connectivity()
        except Exception as e:
            self.stderr.write(f"Neo4j connection failed: {e}")
            return

        self.stdout.write("Connected. Building graph…")

        with driver.session() as s:
            self._clear(s)
            self._create_indexes(s)
            rows = self._load_csv(csv_path)
            self._create_nodes_and_rels(s, rows)
            self._add_co_relationships(s)

        driver.close()
        self.stdout.write(self.style.SUCCESS("KB Graph built successfully!"))

    # ── helpers ──────────────────────────────────────────────────────────────

    def _clear(self, session):
        self.stdout.write("  Clearing existing graph…")
        session.run("MATCH (n) DETACH DELETE n")

    def _create_indexes(self, session):
        session.run("CREATE INDEX user_idx  IF NOT EXISTS FOR (u:User)    ON (u.id)")
        session.run("CREATE INDEX prod_idx  IF NOT EXISTS FOR (p:Product) ON (p.id)")

    def _load_csv(self, path):
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.stdout.write(f"  Loaded {len(rows)} rows")
        return rows

    def _create_nodes_and_rels(self, session, rows):
        self.stdout.write("  Creating nodes and relationships…")
        for i, row in enumerate(rows):
            uid = row["user_id"]
            pid = row["product_id"]
            act = row["action"]
            ts  = row["timestamp"]
            rel = ACTION_TO_REL.get(act, "INTERACTED")

            session.run(
                f"""
                MERGE (u:User {{id: $uid}})
                MERGE (p:Product {{id: $pid}})
                CREATE (u)-[:{rel} {{timestamp: $ts, action: $act}}]->(p)
                """,
                uid=uid, pid=pid, ts=ts, act=act,
            )

            if (i + 1) % 500 == 0:
                self.stdout.write(f"    {i + 1}/{len(rows)} rows processed")

        self.stdout.write(f"  All {len(rows)} rows inserted")

    def _add_co_relationships(self, session):
        self.stdout.write("  Building co-purchase relationships…")
        session.run("""
            MATCH (u:User)-[:ADDED_TO_CART]->(p1:Product),
                  (u)-[:ADDED_TO_CART]->(p2:Product)
            WHERE p1.id < p2.id
            WITH p1, p2, count(u) AS co
            WHERE co >= 2
            MERGE (p1)-[r:CO_PURCHASED_WITH]->(p2)
            ON CREATE SET r.count = co
            ON MATCH  SET r.count = co
        """)

        self.stdout.write("  Building co-view relationships…")
        session.run("""
            MATCH (u:User)-[:VIEWED]->(p1:Product),
                  (u)-[:VIEWED]->(p2:Product)
            WHERE p1.id < p2.id
            WITH p1, p2, count(u) AS co
            WHERE co >= 3
            MERGE (p1)-[r:CO_VIEWED_WITH]->(p2)
            ON CREATE SET r.count = co
            ON MATCH  SET r.count = co
        """)
        self.stdout.write("  Co-relationships done")
