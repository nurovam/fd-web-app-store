import type { FC } from "react";

type HeroProps = {
  onViewCatalog?: () => void;
};

const Hero: FC<HeroProps> = ({ onViewCatalog }) => {
  return (
    <section className="card shadow-sm" style={{ padding: "28px", overflow: "hidden", position: "relative" }}>
      <div
        style={{
          position: "absolute",
          inset: "0",
          background:
            "linear-gradient(135deg, rgba(15,108,206,0.10) 0%, rgba(43,167,255,0.05) 50%, rgba(255,255,255,0.35) 100%)"
        }}
      />
      <div style={{ position: "relative", zIndex: 2, display: "flex", gap: "28px", alignItems: "center" }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="pill">Стоматологический маркетплейс B2B</div>
          <h1 style={{ fontSize: "34px", lineHeight: 1.2, margin: "16px 0 12px", color: "#0f2f6e" }}>
            Стоматологические товары <br /> для клиник и врачей
          </h1>
          <p style={{ color: "#486180", maxWidth: 560, marginBottom: 20 }}>
            Широкий ассортимент инструментов, материалов и расходников. Быстрая доставка, проверенные бренды
            и прозрачные цены.
          </p>
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
            <button className="button" onClick={onViewCatalog}>
              Перейти в каталог
            </button>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontWeight: 700, color: "#0f6cce" }}>5000+</span>
              <span style={{ color: "#486180" }}>товаров в наличии</span>
            </div>
          </div>
        </div>
        <div style={{ flex: 1, display: "flex", justifyContent: "center" }}>
          <img
            src="https://images.unsplash.com/photo-1582719478180-2b1f83a62d1d?auto=format&fit=crop&w=1100&q=80"
            alt="Dental instruments"
            style={{ width: "100%", maxWidth: 540, borderRadius: 18, boxShadow: "0 18px 40px rgba(15,108,206,0.20)" }}
          />
        </div>
      </div>
    </section>
  );
};

export default Hero;
