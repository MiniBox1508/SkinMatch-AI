import os
import time
from PIL import Image
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

class GeminiSmartRouter:
    def __init__(self, api_key):
        # Cấu hình khóa xác thực duy nhất cho toàn bộ Project
        genai.configure(api_key=api_key)
        
        # BƯỚC 1: KHỞI TẠO BỘ ĐỆM BẰNG GIẢ ĐỊNH LẠC QUAN (Nạp thông số định biên từ CSV)
        # Các thông số RPM, TPM, RPD được dập khuôn chính xác theo tài liệu hệ thống
        self.model_configs = {
            "gemini-3.1-flash-lite": {"priority": 1, "max_rpm": 15, "max_tpm": 250000, "max_rpd": 500},
            "gemini-2.5-flash-lite": {"priority": 2, "max_rpm": 10, "max_tpm": 250000, "max_rpd": 20},
            "gemini-2.5-flash":      {"priority": 3, "max_rpm": 5,  "max_tpm": 250000, "max_rpd": 20},
            "gemini-3-flash":        {"priority": 4, "max_rpm": 5,  "max_tpm": 250000, "max_rpd": 20},
            "gemini-3.5-flash":      {"priority": 5, "max_rpm": 5,  "max_tpm": 250000, "max_rpd": 20}
        }
        
        # Khởi tạo Local Cache trống trên RAM
        self.local_cache = {}
        for m_id, config in self.model_configs.items():
            self.local_cache[m_id] = {
                "priority": config["priority"],
                "remaining_rpm": config["max_rpm"],
                "remaining_tpm": config["max_tpm"],
                "remaining_rpd": config["max_rpd"],
                "reset_time": 0.0  # 0.0 nghĩa là không bị khóa, sẵn sàng dùng ngay
            }
        print("[GEMINI_ROUTER_LOG] Khoi tao bo dem lac quan thanh cong cho 5 mo hinh.")

    def _get_best_available_model(self):
        """Logic kiểm tra và chọn ra mô hình ưu tiên cao nhất chưa chạm ngưỡng giới hạn"""
        current_time = time.time()
        
        # Sắp xếp danh sách duyệt dựa trên chỉ số Độ ưu tiên (Từ 1 đến 5)
        sorted_models = sorted(self.local_cache.items(), key=lambda x: x[1]["priority"])
        
        for model_name, cache in sorted_models:
            # Nếu đã qua thời gian khóa reset_time, tự động hoàn trả 100% hạn mức định biên
            if current_time > cache["reset_time"]:
                config = self.model_configs[model_name]
                cache["remaining_rpm"] = config["max_rpm"]
                cache["remaining_tpm"] = config["max_tpm"]
                cache["remaining_rpd"] = config["max_rpd"]
                cache["reset_time"] = 0.0
            
            # Điều kiện trích chọn: Cả 3 chỉ số đều phải còn dung lượng hoạt động
            if cache["remaining_rpm"] > 0 and cache["remaining_tpm"] > 0 and cache["remaining_rpd"] > 0:
                return model_name
                
        return None

    def execute_request(self, system_instruction, user_text, pil_image=None):
        """Hàm điều phối trung tâm tiếp nhận yêu cầu từ Frontend Streamlit"""
        full_prompt = f"{system_instruction}\n\nYêu cầu khách hàng: {user_text}"
        
        # Vòng lặp tối đa 5 lần bọc lót tương ứng với 5 dòng mô hình sẵn có
        for attempt in range(5):
            selected_model = self._get_best_available_model()
            
            if not selected_model:
                return {"error": "[GEMINI_ROUTER_LOG] Toàn bộ 5 mô hình đều đã chạm ngưỡng giới hạn an toàn!"}
                
            print(f"[GEMINI_ROUTER_LOG] Luot chon [{attempt+1}]: Dinh tuyen yeu cau sang -> {selected_model}")
            
            try:
                # Khởi tạo đối tượng thực thi
                model = genai.GenerativeModel(selected_model)
                content_payload = [full_prompt]
                if pil_image:
                    content_payload.append(pil_image)
                
                # Thực thi gọi lệnh Native SDK chính thức của Google
                response = model.generate_content(
                    contents=content_payload,
                    generation_config={"response_mime_type": "application/json"}
                )
                
                # KỊCH BẢN A: GỌI LỆNH THÀNH CÔNG
                # Cập nhật ước lượng trừ bớt 1 request trong cache (Hoặc đọc chính xác từ response metadata nếu có)
                self.local_cache[selected_model]["remaining_rpm"] -= 1
                print(f"[GEMINI_ROUTER_LOG] Kich ban A kich hoat: {selected_model} thuc thi thanh cong.")
                
                return response.text
                
            except ResourceExhausted as e:
                # KỊCH BẢN B: GẶP LỖI QUÁ TẢI HẠN MỨC (RATE LIMIT 429)
                print(f"[GEMINI_ROUTER_LOG] Kich ban B kich hoat: {selected_model} bao loi can han muc (429).")
                
                # Khóa mô hình cục bộ trong vòng 60 giây (Hoặc bóc tách thời gian chính xác từ lỗi của Google)
                self.local_cache[selected_model]["remaining_rpm"] = 0
                self.local_cache[selected_model]["reset_time"] = time.time() + 60.0
                
                # Vòng lặp tự động chạy tiếp để chuyển hướng sang mô hình ưu tiên kế tiếp
                continue
                
            except Exception as e:
                # Bắt các lỗi kỹ thuật khác (Ví dụ: Lỗi đường truyền, ảnh hỏng)
                return {"error": f"[GEMINI_ROUTER_LOG] Sự cố hệ thống không xác định: {str(e)}"}
                
        return {"error": "[GEMINI_ROUTER_LOG] Quá trình thực thi thất bại sau khi thử sai qua cả 5 mô hình."}

# =====================================================================
# Singleton Logic cho Backend (Streamlit sẽ không làm reset Cache)
# =====================================================================
_global_router_instance = None

def get_router_instance(api_key):
    global _global_router_instance
    if _global_router_instance is None:
        _global_router_instance = GeminiSmartRouter(api_key)
    return _global_router_instance
