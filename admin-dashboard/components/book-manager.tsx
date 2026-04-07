"use client";

import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { createBook, deleteBook, fetchBooks, fetchCatalogs, updateBook, type BookPayload, type BookRecord, type CatalogRecord } from "@/lib/admin-api";
import { getStaffSession, isStaffAuthenticated, logoutStaff } from "@/lib/staff-auth";
import { AlertCircle, ArrowRight, Edit3, Loader2, Plus, RefreshCw, Search, Trash2 } from "lucide-react";

type BookFormState = {
  title: string;
  author: string;
  isbn: string;
  price: string;
  stock: string;
  catalog_id: string;
  description: string;
  image_url: string;
};

const emptyForm: BookFormState = {
  title: "",
  author: "",
  isbn: "",
  price: "",
  stock: "0",
  catalog_id: "",
  description: "",
  image_url: "",
};

function toNumber(value: string) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function BookManager() {
  const [books, setBooks] = useState<BookRecord[]>([]);
  const [catalogs, setCatalogs] = useState<CatalogRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [removingId, setRemovingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [editingBookId, setEditingBookId] = useState<number | null>(null);
  const [form, setForm] = useState<BookFormState>(emptyForm);

  const staffSession = getStaffSession();
  const staffAuthenticated = isStaffAuthenticated();

  const catalogMap = useMemo(() => {
    return new Map(catalogs.map((catalog) => [catalog.id, catalog]));
  }, [catalogs]);

  const filteredBooks = useMemo(() => {
    const term = searchTerm.trim().toLowerCase();
    if (!term) {
      return books;
    }

    return books.filter((book) => {
      return [
        book.title,
        book.author,
        book.isbn,
        book.description,
        catalogMap.get(book.catalog_id)?.name || "",
      ]
        .join(" ")
        .toLowerCase()
        .includes(term);
    });
  }, [books, catalogMap, searchTerm]);

  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [bookData, catalogData] = await Promise.all([fetchBooks(), fetchCatalogs()]);
      setBooks(bookData);
      setCatalogs(catalogData);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Không thể tải dữ liệu sách";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const resetForm = () => {
    setForm(emptyForm);
    setEditingBookId(null);
  };

  const beginEdit = (book: BookRecord) => {
    setEditingBookId(book.id);
    setForm({
      title: book.title,
      author: book.author,
      isbn: book.isbn,
      price: String(book.price),
      stock: String(book.stock),
      catalog_id: String(book.catalog_id),
      description: book.description || "",
      image_url: book.image_url || "",
    });
  };

  const submitBook = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setError(null);

    try {
      const payload: BookPayload = {
        title: form.title.trim(),
        author: form.author.trim(),
        isbn: form.isbn.trim(),
        price: toNumber(form.price),
        stock: toNumber(form.stock),
        catalog_id: toNumber(form.catalog_id),
        description: form.description.trim(),
        image_url: form.image_url.trim(),
        created_by_staff_id: staffSession?.userId ?? null,
      };

      if (editingBookId) {
        await updateBook(editingBookId, payload);
      } else {
        await createBook(payload);
      }

      await loadData();
      resetForm();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Không thể lưu sách";
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  const removeBook = async (book: BookRecord) => {
    const confirmed = window.confirm(`Xóa sách "${book.title}"?`);
    if (!confirmed) {
      return;
    }

    setRemovingId(book.id);
    setError(null);

    try {
      await deleteBook(book.id);
      await loadData();
      if (editingBookId === book.id) {
        resetForm();
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Không thể xóa sách";
      setError(message);
    } finally {
      setRemovingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <Card className="border-primary/20 bg-gradient-to-r from-primary/5 via-background to-background">
        <CardHeader>
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <CardTitle>Quản lý sách cho staff</CardTitle>
              <CardDescription>
                Tạo, sửa, xóa và cập nhật dữ liệu sách từ book-service.
              </CardDescription>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {staffAuthenticated ? (
                <div className="rounded-full border border-green-500/20 bg-green-500/10 px-3 py-1 text-sm text-green-700">
                  Đã đăng nhập staff: {staffSession?.username}
                </div>
              ) : (
                <div className="rounded-full border border-amber-500/20 bg-amber-500/10 px-3 py-1 text-sm text-amber-700">
                  Chưa đăng nhập staff
                </div>
              )}
              <Button variant="outline" size="sm" onClick={loadData}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Tải lại
              </Button>
              {staffAuthenticated ? (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    logoutStaff();
                    window.location.reload();
                  }}
                >
                  Đăng xuất staff
                </Button>
              ) : null}
            </div>
          </div>
        </CardHeader>
      </Card>

      {error ? (
        <Card className="border-destructive/30 bg-destructive/5">
          <CardContent className="flex items-start gap-3 py-4">
            <AlertCircle className="mt-0.5 h-5 w-5 text-destructive" />
            <div>
              <p className="font-medium text-destructive">Có lỗi xảy ra</p>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
          </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[360px_minmax(0,1fr)]">
        <Card>
          <CardHeader>
            <CardTitle>{editingBookId ? "Sửa sách" : "Thêm sách mới"}</CardTitle>
            <CardDescription>
              {staffAuthenticated
                ? "Nhập thông tin sách để lưu vào book-service."
                : "Bạn cần đăng nhập staff để thực hiện tạo hoặc cập nhật sách."}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={submitBook}>
              <div className="space-y-2">
                <label className="text-sm font-medium">Tên sách</label>
                <Input
                  value={form.title}
                  onChange={(e) => setForm((current) => ({ ...current, title: e.target.value }))}
                  placeholder="Nhập tên sách"
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Tác giả</label>
                <Input
                  value={form.author}
                  onChange={(e) => setForm((current) => ({ ...current, author: e.target.value }))}
                  placeholder="Nhập tên tác giả"
                  required
                />
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-sm font-medium">ISBN</label>
                  <Input
                    value={form.isbn}
                    onChange={(e) => setForm((current) => ({ ...current, isbn: e.target.value }))}
                    placeholder="13 ký tự"
                    maxLength={13}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Giá</label>
                  <Input
                    type="number"
                    min="0"
                    step="0.01"
                    value={form.price}
                    onChange={(e) => setForm((current) => ({ ...current, price: e.target.value }))}
                    placeholder="0"
                    required
                  />
                </div>
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Tồn kho</label>
                  <Input
                    type="number"
                    min="0"
                    step="1"
                    value={form.stock}
                    onChange={(e) => setForm((current) => ({ ...current, stock: e.target.value }))}
                    placeholder="0"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Danh mục</label>
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={form.catalog_id}
                    onChange={(e) => setForm((current) => ({ ...current, catalog_id: e.target.value }))}
                    required
                  >
                    <option value="">Chọn danh mục</option>
                    {catalogs.map((catalog) => (
                      <option key={catalog.id} value={catalog.id}>
                        {catalog.icon} {catalog.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Ảnh bìa URL</label>
                <Input
                  value={form.image_url}
                  onChange={(e) => setForm((current) => ({ ...current, image_url: e.target.value }))}
                  placeholder="https://..."
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Mô tả</label>
                <textarea
                  className="min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none ring-offset-background placeholder:text-muted-foreground focus:ring-2 focus:ring-ring focus:ring-offset-2"
                  value={form.description}
                  onChange={(e) => setForm((current) => ({ ...current, description: e.target.value }))}
                  placeholder="Nhập mô tả sách"
                />
              </div>

              <div className="flex flex-wrap gap-2">
                <Button type="submit" disabled={saving || !staffAuthenticated}>
                  {saving ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Đang lưu...
                    </>
                  ) : editingBookId ? (
                    <>
                      <Edit3 className="mr-2 h-4 w-4" />
                      Cập nhật sách
                    </>
                  ) : (
                    <>
                      <Plus className="mr-2 h-4 w-4" />
                      Tạo sách
                    </>
                  )}
                </Button>
                <Button type="button" variant="outline" onClick={resetForm}>
                  Xóa form
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <CardTitle>Danh sách sách</CardTitle>
                <CardDescription>
                  Quản lý trực tiếp dữ liệu sách trong book-service.
                </CardDescription>
              </div>
              <div className="relative w-full lg:max-w-xs">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-10"
                  placeholder="Tìm theo tên, tác giả, ISBN..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>
            <p className="text-sm text-muted-foreground">
              Tổng số: {filteredBooks.length} / {books.length} sách
            </p>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center rounded-lg border py-16 text-muted-foreground">
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Đang tải dữ liệu...
              </div>
            ) : (
              <div className="overflow-x-auto rounded-lg border">
                <table className="w-full text-sm">
                  <thead className="bg-muted/60 text-left text-xs uppercase tracking-wide text-muted-foreground">
                    <tr>
                      <th className="px-4 py-3">Sách</th>
                      <th className="px-4 py-3">ISBN</th>
                      <th className="px-4 py-3">Danh mục</th>
                      <th className="px-4 py-3">Giá</th>
                      <th className="px-4 py-3">Tồn kho</th>
                      <th className="px-4 py-3 text-right">Thao tác</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredBooks.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="px-4 py-10 text-center text-muted-foreground">
                          Không có sách nào phù hợp.
                        </td>
                      </tr>
                    ) : (
                      filteredBooks.map((book) => (
                        <tr key={book.id} className="border-t">
                          <td className="px-4 py-3 align-top">
                            <div className="font-medium">{book.title}</div>
                            <div className="max-w-[320px] truncate text-xs text-muted-foreground">
                              {book.author}
                            </div>
                            <div className="max-w-[320px] truncate text-xs text-muted-foreground">
                              {book.description || "Không có mô tả"}
                            </div>
                          </td>
                          <td className="px-4 py-3 align-top font-mono text-xs">{book.isbn}</td>
                          <td className="px-4 py-3 align-top">
                            {catalogMap.get(book.catalog_id)?.icon} {catalogMap.get(book.catalog_id)?.name || book.catalog_id}
                          </td>
                          <td className="px-4 py-3 align-top">{Number(book.price).toLocaleString("vi-VN")} đ</td>
                          <td className="px-4 py-3 align-top">{book.stock}</td>
                          <td className="px-4 py-3 align-top">
                            <div className="flex justify-end gap-2">
                              <Button type="button" variant="outline" size="sm" onClick={() => beginEdit(book)}>
                                <Edit3 className="mr-2 h-4 w-4" />
                                Sửa
                              </Button>
                              <Button
                                type="button"
                                variant="destructive"
                                size="sm"
                                disabled={removingId === book.id || !staffAuthenticated}
                                onClick={() => removeBook(book)}
                              >
                                {removingId === book.id ? (
                                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                ) : (
                                  <Trash2 className="mr-2 h-4 w-4" />
                                )}
                                Xóa
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="flex flex-col gap-3 p-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="font-medium">Cần đăng nhập staff?</p>
            <p className="text-sm text-muted-foreground">
              Dùng trang đăng nhập riêng để lấy JWT role staff, sau đó quay lại trang sách.
            </p>
          </div>
          <Button type="button" variant="outline" asChild>
            <a href="/login">
              Đi tới trang đăng nhập <ArrowRight className="ml-2 h-4 w-4" />
            </a>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}