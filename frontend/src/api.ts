import axios from "axios";
import type { Product, Category } from "./types";
import { sampleCategories, sampleProducts } from "./data";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api/",
  timeout: 5000
});

export async function fetchProducts(): Promise<Product[]> {
  try {
    const { data } = await api.get<Product[]>("products/");
    return data;
  } catch (error) {
    console.warn("Falling back to sample products", error);
    return sampleProducts;
  }
}

export async function fetchCategories(): Promise<Category[]> {
  try {
    const { data } = await api.get<Category[]>("categories/");
    return data;
  } catch (error) {
    console.warn("Falling back to sample categories", error);
    return sampleCategories;
  }
}

export async function addToCart(productId: number, quantity = 1) {
  return api.post("cart/add/", { product_id: productId, quantity });
}
