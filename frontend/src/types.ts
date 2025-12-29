export type Category = {
  id: number;
  name: string;
  slug?: string;
  description?: string;
  image_url?: string;
};

export type Product = {
  id: number;
  title: string;
  sku: string;
  price: number;
  currency: string;
  hero_image?: string;
  description?: string;
  inventory: number;
  is_featured?: boolean;
  category?: Category;
};

export type Feature = {
  title: string;
  description: string;
  icon: string;
};
