import type { FC } from "react";
import type { Category } from "../types";

type Props = {
  categories: Category[];
  onOpenCatalog?: () => void;
};

const icons = ["🧰", "🦷", "📦", "💉", "🛠️", "⚙️", "💊", "🧪"];

const CategoryGrid: FC<Props> = ({ categories, onOpenCatalog }) => {
  return (
    <section className="card" style={{ padding: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <div>
          <h2 className="section-title">Каталог</h2>
          <p className="section-subtitle">Категории по направлениям клиник и кабинетов</p>
        </div>
        <button className="button" style={{ paddingInline: 16 }} onClick={onOpenCatalog}>
          В каталог
        </button>
      </div>
      <div className="grid cols-4">
        {categories.map((category, index) => (
          <div
            key={category.id}
            className="card"
            style={{ padding: 16, border: "1px solid #e6eef7", display: "flex", alignItems: "center", gap: 12 }}
          >
            <div
              style={{
                width: 46,
                height: 46,
                borderRadius: 14,
                background: "#f4f7fc",
                display: "grid",
                placeItems: "center",
                fontSize: 22
              }}
            >
              {icons[index % icons.length]}
            </div>
            <div style={{ fontWeight: 600, color: "#1f2f44" }}>{category.name}</div>
          </div>
        ))}
      </div>
    </section>
  );
};

export default CategoryGrid;
