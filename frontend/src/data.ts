import type { Category, Product, Feature } from "./types";

export const sampleCategories: Category[] = [
  { id: 1, name: "Инструменты", slug: "instruments" },
  { id: 2, name: "Наборы боров", slug: "bor-sets" },
  { id: 3, name: "Расходные материалы", slug: "consumables" },
  { id: 4, name: "Стоматологические материалы", slug: "materials" },
  { id: 5, name: "Анестезия", slug: "anesthesia" },
  { id: 6, name: "Оборудование", slug: "equipment" }
];

export const sampleProducts: Product[] = [
  {
    id: 100,
    title: "Эндомотор VDW Gold RECIPROC",
    sku: "FD-001",
    price: 45500,
    currency: "₽",
    inventory: 10,
    hero_image: "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=900&q=80",
    description: "Умный эндомотор с адаптивными режимами для точной обработки каналов."
  },
  {
    id: 101,
    title: "Боры алмазные (набор 10 шт.)",
    sku: "FD-002",
    price: 1200,
    currency: "₽",
    inventory: 50,
    hero_image: "https://images.unsplash.com/photo-1582719478171-2f2df43fb8c8?auto=format&fit=crop&w=900&q=80",
    description: "Набор универсальных боров для ежедневных вмешательств.",
    is_featured: true
  },
  {
    id: 102,
    title: "Интравазальный скалер (набор 10 шт.)",
    sku: "FD-003",
    price: 23900,
    currency: "₽",
    inventory: 8,
    hero_image: "https://images.unsplash.com/photo-1613758742505-0b0c85e988c1?auto=format&fit=crop&w=900&q=80",
    description: "Высокоточный набор скалеров с цветовой маркировкой."
  },
  {
    id: 103,
    title: "Адгезив 3M Single Bond Universal, 5 мл",
    sku: "FD-004",
    price: 4200,
    currency: "₽",
    inventory: 30,
    hero_image: "https://images.unsplash.com/photo-1586015555751-63bb77f632b0?auto=format&fit=crop&w=900&q=80",
    description: "Надёжный универсальный адгезив для ежедневной практики."
  }
];

export const features: Feature[] = [
  { title: "Гарантия качества", description: "Сертифицированные поставки и контроль логистики.", icon: "✅" },
  { title: "Проверенные бренды", description: "Только надёжные производители для клиник и врачей.", icon: "⭐" },
  { title: "Быстрая доставка", description: "Оперативно доставим по РФ и СНГ, статус отслеживается.", icon: "🚚" },
  { title: "Поддержка стоматологов", description: "Поможем подобрать расходники и оборудование.", icon: "🧑‍⚕️" }
];
