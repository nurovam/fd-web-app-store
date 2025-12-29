import { useEffect, useMemo, useRef, useState } from "react";
import CategoryGrid from "./components/CategoryGrid";
import FeatureStrip from "./components/FeatureStrip";
import Header from "./components/Header";
import Hero from "./components/Hero";
import ProductCard from "./components/ProductCard";
import { fetchCategories, fetchProducts, addToCart } from "./api";
import { features } from "./data";
import type { Category, Product } from "./types";

function App() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [status, setStatus] = useState<string>("");
  const catalogRef = useRef<HTMLDivElement | null>(null);
  const productsRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    fetchCategories().then(setCategories);
    fetchProducts().then(setProducts);
  }, []);

  const featured = useMemo(() => products.filter((p) => p.is_featured).slice(0, 4), [products]);

  const handleAddToCart = async (product: Product) => {
    setStatus(`Добавляем ${product.title}...`);
    try {
      await addToCart(product.id, 1);
      setStatus(`Товар "${product.title}" добавлен в корзину`);
    } catch (error) {
      console.error(error);
      setStatus("Не удалось добавить в корзину (проверьте API)");
    }
    setTimeout(() => setStatus(""), 2500);
  };

  const handleScrollToCatalog = () => {
    catalogRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const handleScrollToProducts = () => {
    productsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const handleLoginClick = () => {
    setStatus("Авторизация откроется в отдельной форме. Пока можно пользоваться гостевым просмотром каталога.");
    setTimeout(() => setStatus(""), 3500);
  };

  return (
    <div className="page">
      <Header onLogin={handleLoginClick} onOpenCatalog={handleScrollToCatalog} onOpenSales={handleScrollToProducts} />
      <div style={{ display: "grid", gap: 20, marginTop: 18 }}>
        <Hero onViewCatalog={handleScrollToCatalog} />
        <div ref={catalogRef}>
          <CategoryGrid categories={categories} onOpenCatalog={handleScrollToProducts} />
        </div>
        <section className="card" style={{ padding: 20 }} ref={productsRef}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
            <div>
              <h2 className="section-title">Популярные товары</h2>
              <p className="section-subtitle">Хиты продаж и быстрый выбор для закупок</p>
            </div>
            <div className="chips">
              <span className="pill">Новинки</span>
              <span className="pill">Скидки</span>
              <span className="pill">В наличии</span>
            </div>
          </div>
          <div className="grid cols-4">
            {(featured.length ? featured : products).map((product) => (
              <ProductCard key={product.id} product={product} onAdd={handleAddToCart} />
            ))}
          </div>
          {status && (
            <div
              className="card"
              style={{
                marginTop: 12,
                padding: 14,
                background: "#eaf4ff",
                color: "#0f4da8",
                border: "1px solid #cbe0ff",
                fontWeight: 600
              }}
            >
              {status}
            </div>
          )}
        </section>
        <FeatureStrip items={features} />
        <div className="card" style={{ padding: 16 }}>
          <div className="logo-row">
            {["3M", "EMS", "GC", "Dentsply", "Kerr", "Curaprox", "OMNIA", "Coltene"].map((brand) => (
              <span key={brand} style={{ textAlign: "center", fontWeight: 700, color: "#6d7f99" }}>
                {brand}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
