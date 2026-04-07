import { apiClient } from "./api";
import { getStaffAuthHeaders } from "./staff-auth";

export interface CatalogRecord {
  id: number;
  name: string;
  description: string;
  icon: string;
  created_at: string;
  updated_at: string;
}

export interface BookRecord {
  id: number;
  title: string;
  author: string;
  isbn: string;
  price: string;
  stock: number;
  catalog_id: number;
  description: string;
  image_url: string;
  created_by_staff_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface BookPayload {
  title: string;
  author: string;
  isbn: string;
  price: number;
  stock: number;
  catalog_id: number;
  description: string;
  image_url: string;
  created_by_staff_id?: number | null;
}

export async function fetchBooks() {
  const response = await apiClient.get("/api/books/books/");
  return response.data as BookRecord[];
}

export async function fetchCatalogs() {
  const response = await apiClient.get("/api/catalogs/catalogs/");
  return response.data as CatalogRecord[];
}

export async function createBook(payload: BookPayload) {
  const response = await apiClient.post("/api/books/books/", payload, {
    headers: getStaffAuthHeaders(),
  });
  return response.data as BookRecord;
}

export async function updateBook(id: number, payload: Partial<BookPayload>) {
  const response = await apiClient.patch(`/api/books/books/${id}/`, payload, {
    headers: getStaffAuthHeaders(),
  });
  return response.data as BookRecord;
}

export async function deleteBook(id: number) {
  await apiClient.delete(`/api/books/books/${id}/`, {
    headers: getStaffAuthHeaders(),
  });
}