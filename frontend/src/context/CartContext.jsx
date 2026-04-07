import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import { cartService } from "../services";
import { useAuth } from "./AuthContext";
import { toast } from "react-toastify";

const CartContext = createContext(null);

export function CartProvider({ children }) {
  const { customer, isAuthenticated } = useAuth();
  const [cart, setCart] = useState({ items: [], total: 0 });
  const [loading, setLoading] = useState(false);

  const fetchCart = useCallback(async () => {
    if (!isAuthenticated || !customer?.id) return;

    setLoading(true);
    try {
      const response = await cartService.getCart(customer.id);
      const cartData = response.data;

      // Cart items đã có book data từ backend
      const itemsWithBooks = (cartData.items || []).map((item) => ({
        ...item,
        book: item.book || null,
      }));

      const total = itemsWithBooks.reduce((sum, item) => {
        if (item.book) {
          return sum + parseFloat(item.book.price) * item.quantity;
        }
        return sum;
      }, 0);

      setCart({ items: itemsWithBooks, total });
    } catch (error) {
      // Cart không tồn tại - sẽ tự tạo khi thêm item
      setCart({ items: [], total: 0 });
    } finally {
      setLoading(false);
    }
  }, [customer?.id, isAuthenticated]);

  useEffect(() => {
    fetchCart();
  }, [fetchCart]);

  const addItem = async (bookId, quantity = 1) => {
    if (!isAuthenticated) {
      toast.warning("Vui lòng đăng nhập để thêm vào giỏ hàng");
      return false;
    }

    try {
      await cartService.addItem(customer.id, bookId, quantity);
      await fetchCart();
      toast.success("Đã thêm vào giỏ hàng");
      return true;
    } catch (error) {
      toast.error(error.response?.data?.error || "Không thể thêm vào giỏ hàng");
      return false;
    }
  };

  const updateItem = async (bookId, quantity) => {
    try {
      await cartService.updateItem(customer.id, bookId, quantity);
      await fetchCart();
      return true;
    } catch (error) {
      toast.error("Không thể cập nhật số lượng");
      return false;
    }
  };

  const removeItem = async (bookId) => {
    try {
      await cartService.removeItem(customer.id, bookId);
      await fetchCart();
      toast.success("Đã xóa khỏi giỏ hàng");
      return true;
    } catch (error) {
      toast.error("Không thể xóa sản phẩm");
      return false;
    }
  };

  const clearCart = async () => {
    try {
      await cartService.clearCart(customer.id);
      setCart({ items: [], total: 0 });
      return true;
    } catch (error) {
      toast.error("Không thể xóa giỏ hàng");
      return false;
    }
  };

  const itemCount = cart.items.reduce((sum, item) => sum + item.quantity, 0);

  return (
    <CartContext.Provider
      value={{
        cart,
        loading,
        itemCount,
        addItem,
        updateItem,
        removeItem,
        clearCart,
        fetchCart,
      }}
    >
      {children}
    </CartContext.Provider>
  );
}

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error("useCart must be used within a CartProvider");
  }
  return context;
};
