import pandas as pd
import json

class DataProcessor:
    def __init__(self, data_path="DATASET/master_cosmetics_dataset.csv"):
        try:
            self.df = pd.read_csv(data_path)
            # Ensure price is integer
            if 'Price' in self.df.columns:
                self.df['Price'] = pd.to_numeric(self.df['Price'], errors='coerce').fillna(0).astype(int)
        except Exception as e:
            print(f"Error loading dataset: {e}")
            self.df = pd.DataFrame()

    def filter_candidates(self, categories, skin_types, skin_concerns, min_price, max_price, max_retries=3):
        """
        Lọc ứng viên theo Sidebar + Fallback Price Loosening.
        """
        if self.df.empty:
            return []

        current_max_price = max_price

        for attempt in range(max_retries + 1):
            mask = pd.Series([True] * len(self.df))

            if categories:
                # Nếu cột Category chứa 1 trong các giá trị categories
                mask &= self.df['Category'].isin(categories)

            if skin_types:
                # Nếu bất kỳ loại da nào trong skin_types xuất hiện trong cột Skin_Type
                skin_type_mask = pd.Series([False] * len(self.df))
                for st in skin_types:
                    skin_type_mask |= self.df['Skin_Type'].str.contains(st, case=False, na=False)
                mask &= skin_type_mask

            if skin_concerns:
                # Nếu bất kỳ tình trạng da nào trong skin_concerns xuất hiện trong cột Skin_Concern
                concern_mask = pd.Series([False] * len(self.df))
                for sc in skin_concerns:
                    concern_mask |= self.df['Skin_Concern'].str.contains(sc, case=False, na=False)
                mask &= concern_mask

            # Lọc theo giá
            mask &= (self.df['Price'] >= min_price) & (self.df['Price'] <= current_max_price)

            filtered_df = self.df[mask]

            if not filtered_df.empty:
                # Nếu có kết quả, trả về list dict
                # Trộn ngẫu nhiên và lấy tối đa 20 sản phẩm để không làm quá tải Gemini
                if len(filtered_df) > 20:
                    filtered_df = filtered_df.sample(20)
                
                return filtered_df.to_dict(orient='records')
            
            # Fallback Price Loosening: tăng giá trần 20%
            current_max_price = int(current_max_price * 1.2)

        return []

    def get_candidates_json(self, candidates):
        """
        Chuyển list candidates sang JSON string để đưa vào prompt
        """
        # Giảm thiểu các trường không cần thiết để tiết kiệm token
        minimized_candidates = []
        for c in candidates:
            minimized_candidates.append({
                "Product_Name": c.get("Product_Name", ""),
                "Brand": c.get("Brand", ""),
                "Category": c.get("Category", ""),
                "Skin_Type": c.get("Skin_Type", ""),
                "Skin_Concern": c.get("Skin_Concern", ""),
                "Texture": c.get("Texture", ""),
                "Product_Pic": c.get("Product_Pic", ""),
                "Product_URL": c.get("Product_URL", ""),
                "Description": c.get("Description", ""),
                "Uses": c.get("Uses", ""),
                "Usage": c.get("Usage", ""),
                "Reviews": c.get("Reviews", ""),
                "Price": c.get("Price", 0)
            })
        return json.dumps(minimized_candidates, ensure_ascii=False)
