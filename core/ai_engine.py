import os
import json
from pydantic import BaseModel, Field
from typing import Optional, List
from PIL import Image
from core.gemini_router_engine import get_router_instance

class RecommendedProduct(BaseModel):
    Product_Name: str = Field(description="Tên sản phẩm")
    Product_Pic: str = Field(description="Link ảnh sản phẩm")
    Product_URL: str = Field(description="Đường link mua hoặc xem chi tiết sản phẩm")
    Price: int = Field(description="Giá sản phẩm")
    Match_Reason: str = Field(description="Lý do khoa học thuyết phục tại sao sản phẩm này giải quyết được vấn đề da của người dùng")
    Usage: str = Field(description="Hướng dẫn sử dụng tối ưu hóa dựa trên thông tin gốc")

class SkinMatchOutputSchema(BaseModel):
    is_valid_image: bool = Field(description="Xác thực ảnh da hoặc nhãn mỹ phẩm. True nếu hợp lệ, False nếu là ảnh rác.")
    error_code: Optional[str] = Field(description="Trả về 'invalid_image' nếu ảnh rác")
    recommended_products: List[RecommendedProduct] = Field(description="Danh sách Top 3 sản phẩm được gợi ý")

class GeminiReranker:
    def __init__(self, api_key=None, model_name=None):
        self.api_key = api_key or os.getenv("AI_API_KEY", "")
        # Gọi Singleton của Smart Router (Chỉ khởi tạo 1 lần duy nhất để giữ trạng thái Cache)
        if self.api_key:
            self.router = get_router_instance(api_key=self.api_key)
        else:
            self.router = None
            
        # Biến này được giữ lại vì tính tương thích ngược, tuy nhiên router tự quyết định model
        self.model_name = model_name or os.getenv("AI_MODEL_NAME", "gemini-3.1-flash-lite")

    def generate_skin_match_native(self, user_text, uploaded_image, pandas_filtered_candidates_json, prompt_template_path="SPEC/MAIN_PROMPT.txt"):
        """
        Gửi request qua giao thức Native Google SDK bằng GeminiSmartRouter.
        """
        if not self.router:
            return None

        try:
            with open(prompt_template_path, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
        except FileNotFoundError:
            prompt_template = "Phân tích ảnh và văn bản đầu vào: {user_text}. Chọn Top 3 sản phẩm từ danh sách: {pandas_filtered_candidates_json}"

        user_prompt_combined = prompt_template.replace("{user_text}", user_text if user_text else "Không có văn bản mô tả")
        user_prompt_combined = user_prompt_combined.replace("{pandas_filtered_candidates_json}", pandas_filtered_candidates_json)
        
        # Pydantic V2 dùng model_json_schema, V1 dùng schema_json. Thử handle an toàn:
        try:
            schema_str = json.dumps(SkinMatchOutputSchema.model_json_schema())
        except AttributeError:
            schema_str = SkinMatchOutputSchema.schema_json()

        system_instruction = f"Bạn là AI chuyên gia da liễu. TRẢ VỀ DUY NHẤT CHUỖI JSON ĐÚNG ĐỊNH DẠNG SAU, KHÔNG GIẢI THÍCH GÌ THÊM:\n{schema_str}"

        try:
            pil_image = None
            if uploaded_image is not None:
                pil_image = Image.open(uploaded_image)
                if pil_image.mode != "RGB":
                    pil_image = pil_image.convert("RGB")

            # Uỷ thác hoàn toàn việc định tuyến, quản lý giới hạn tần suất cho Smart Router
            result_text_or_dict = self.router.execute_request(
                system_instruction=system_instruction,
                user_text=user_prompt_combined,
                pil_image=pil_image
            )
            
            # Nếu Router trả về dict báo lỗi (do thử hết 5 mô hình đều thất bại)
            if isinstance(result_text_or_dict, dict) and "error" in result_text_or_dict:
                error_msg = result_text_or_dict["error"]
                with open("error_logs.md", "a", encoding="utf-8") as f:
                    f.write(f"{error_msg}\n")
                print(error_msg.encode('ascii', 'replace').decode('ascii'))
                return None
                
            result_text = result_text_or_dict or ""
            
            # Robust JSON extraction to handle model hallucinations
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(0)
                
            return result_text.strip() if result_text else ""
            
        except Exception as e:
            error_msg = f"[GEMINI_ROUTER_LOG] Uncaught Exception in ai_engine: {repr(e)}"
            with open("error_logs.md", "a", encoding="utf-8") as f:
                f.write(error_msg + "\n")
            print(error_msg.encode('ascii', 'replace').decode('ascii'))
            return None
