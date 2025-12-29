import type { FC } from "react";

type HeaderProps = {
  onLogin?: () => void;
  onOpenCatalog?: () => void;
  onOpenSales?: () => void;
};

const Header: FC<HeaderProps> = ({ onLogin, onOpenCatalog, onOpenSales }) => {
  return (
    <header
      className="card"
      style={{
        padding: "14px 18px",
        display: "flex",
        alignItems: "center",
        gap: 18,
        position: "sticky",
        top: 12,
        zIndex: 10
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div
          style={{
            width: 44,
            height: 44,
            borderRadius: 12,
            background: "linear-gradient(145deg, #0f6cce, #0b5aab)",
            display: "grid",
            placeItems: "center",
            color: "#fff",
            fontWeight: 800
          }}
        >
          FD
        </div>
        <div>
          <div style={{ fontWeight: 800, fontSize: 18 }}>FamilyDent Shop</div>
          <div style={{ color: "#6d7f99", fontSize: 12 }}>B2B маркетплейс</div>
        </div>
      </div>
      <nav style={{ display: "flex", gap: 14, color: "#3c4d65", fontWeight: 600 }}>
        <button onClick={onOpenCatalog} className="button" style={{ padding: "8px 12px", boxShadow: "none" }}>
          Каталог
        </button>
        <button onClick={onOpenSales} className="button" style={{ padding: "8px 12px", boxShadow: "none" }}>
          Акции
        </button>
        <a href="#" style={{ padding: "8px 12px" }}>
          О компании
        </a>
      </nav>
      <div style={{ flex: 1, display: "flex", justifyContent: "center" }}>
        <div
          style={{
            background: "#f4f7fb",
            border: "1px solid #d9e3f4",
            borderRadius: 12,
            padding: "10px 12px",
            width: "100%",
            maxWidth: 420,
            display: "flex",
            alignItems: "center",
            gap: 8
          }}
        >
          <span role="img" aria-label="search">
            🔍
          </span>
          <input
            type="search"
            placeholder="Поиск товаров..."
            style={{
              border: "none",
              background: "transparent",
              width: "100%",
              outline: "none",
              fontSize: 14
            }}
          />
        </div>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 14, color: "#0f6cce", fontWeight: 700 }}>
        <button onClick={onLogin} className="button" style={{ paddingInline: 14 }}>
          Войти
        </button>
      </div>
    </header>
  );
};

export default Header;
