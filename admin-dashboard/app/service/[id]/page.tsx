"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { DataTable } from "@/components/data-table";
import { Button } from "@/components/ui/button";
import { services, fetchServiceData } from "@/lib/api";
import { ArrowLeft, AlertCircle, Loader2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { BookManager } from "@/components/book-manager";

export default function ServicePage() {
  const params = useParams();
  const router = useRouter();
  const serviceId = params.id as string;

  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const service = services.find((s) => s.id === serviceId);

  const loadData = async () => {
    if (!service) return;

    setLoading(true);
    setError(null);

    try {
      const result = await fetchServiceData(service.endpoint);
      // Handle both array and object responses
      const dataArray = Array.isArray(result) ? result : result.results || [];
      setData(dataArray);
    } catch (err: any) {
      setError(err.message || "Không thể tải dữ liệu");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [serviceId]);

  if (!service) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card>
          <CardContent className="py-12 text-center">
            <AlertCircle className="w-12 h-12 mx-auto mb-4 text-destructive" />
            <p className="text-xl font-semibold mb-2">Service không tồn tại</p>
            <Link href="/">
              <Button className="mt-4">Quay lại trang chủ</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <Link href="/">
          <Button variant="ghost" className="mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Quay lại
          </Button>
        </Link>

        <div className="flex items-center gap-3 mb-2">
          <div
            className={`text-3xl w-12 h-12 flex items-center justify-center rounded-lg ${service.color} text-white`}
          >
            {service.icon}
          </div>
          <div>
            <h1 className="text-3xl font-bold">{service.displayName}</h1>
            <p className="text-muted-foreground">{service.description}</p>
          </div>
        </div>
      </div>

      {service.id === "book" ? (
        <BookManager />
      ) : loading ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Loader2 className="w-8 h-8 mx-auto mb-4 animate-spin text-primary" />
            <p className="text-muted-foreground">Đang tải dữ liệu...</p>
          </CardContent>
        </Card>
      ) : error ? (
        <Card>
          <CardContent className="py-12 text-center">
            <AlertCircle className="w-12 h-12 mx-auto mb-4 text-destructive" />
            <p className="text-xl font-semibold mb-2">Lỗi khi tải dữ liệu</p>
            <p className="text-muted-foreground mb-4">{error}</p>
            <Button onClick={loadData}>Thử lại</Button>
          </CardContent>
        </Card>
      ) : (
        <DataTable
          data={data}
          serviceName={service.displayName}
          onRefresh={loadData}
        />
      )}
    </div>
  );
}
