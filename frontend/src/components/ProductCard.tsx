import type { FC } from "react";
import type { Product } from "../types";

type Props = {
  product: Product;
  onAdd?: (product: Product) => void;
};

const ProductCard: FC<Props> = ({ product, onAdd }) => {
  return (
    <div className="card" style={{ padding: 16, display: "grid", gap: 10 }}>
      {product.is_featured && <span className="badge badge--sale">Хит продаж</span>}
      {product.hero_image && (
        <div
          style={{
            background: "#f7f9fd",
            borderRadius: 12,
            padding: 12,
            border: "1px solid #e6eef7",
            height: 180,
            display: "flex",
            alignItems: "center",
            justifyContent: "center"
          }}
        >
          <img src={product.hero_image} alt={product.title} style={{ maxHeight: "100%", objectFit: "contain" }} />
        </div>
      )}
      <div style={{ minHeight: 72 }}>
        <div style={{ fontWeight: 700, color: "#1a2f52" }}>{product.title}</div>
        <div style={{ color: "#71809b", fontSize: 13, marginTop: 4 }}>SKU: {product.sku}</div>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ fontWeight: 800, fontSize: 18, color: "#0f6cce" }}>
          {product.price.toLocaleString("ru-RU")} {product.currency}
        </span>
        <span style={{ color: "#8292b1" }}>| В наличии: {product.inventory}</span>
      </div>
      <button className="button" onClick={() => onAdd?.(product)}>
        В корзину
      </button>
    </div>
  );
};

export default ProductCard;
