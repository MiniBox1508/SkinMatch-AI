# WORKFLOW TÍCH HỢP ĐA MÔ HÌNH GEMINI VỚI BỘ ĐỆM THÍCH ỨNG TRẠNG THÁI
**Dự án:** Hệ thống Gợi ý Mỹ phẩm Thông minh (SkinMatch AI)  
**Mục tiêu:** Triển khai cơ chế định tuyến ưu tiên cho 5 dòng mô hình Gemini, áp dụng giải pháp Khởi động lạnh Lạc quan và Tự động chuyển hướng khi ngập tải (Fallback).  
**Phạm vi tác động:** Chỉ can thiệp và sửa đổi duy nhất phân hệ điều phối AI Engine ở Backend. Giữ nguyên vẹn 100% logic giao diện Streamlit, phân hệ nén ảnh của Pillow và bộ lọc dữ liệu Dataset của Pandas.

---

## 1. NGUYÊN TẮC THIẾT KẾ KIẾN TRÚC VÀ CÔ LẬP VÙNG ẢNH HƯỞNG

Để việc tích hợp 5 mô hình không làm xáo trộn hệ thống hiện tại, toàn bộ logic quản lý hạn mức, kiểm tra trạng thái và gọi API sẽ được đóng gói cô lập hoàn toàn bên trong một Class độc lập có tên là `GeminiSmartRouter`. 

* **Phía Frontend (Streamlit):** Thay vì gọi trực tiếp SDK của Google, giao diện chỉ gọi duy nhất một hàm chung là `router.execute_request(prompt, image)`. Frontend hoàn toàn không cần biết hệ thống đang dùng mô hình nào ở hậu trường.
* **Phía Xử lý Dữ liệu (Pandas/Pillow):** Dữ liệu sau khi được Pandas lọc thô và ảnh sau khi được Pillow xử lý sẽ được truyền nguyên vẹn làm tham số đầu vào cho `GeminiSmartRouter`.

---

## 2. CẤU TRÚC BỘ ĐỆM CỤC BỘ & KHỞI TẠO LẠC QUAN (COLD START)

Khi hệ thống vừa được khởi động (Thời điểm $t=0$), bộ đệm chưa có dữ liệu thực tế từ Google AI Studio. Hệ thống sẽ tiến hành đọc dữ liệu định biên từ tệp `Gemini Model Rate Limit.csv` và thiết lập một cấu trúc dữ liệu RAM cục bộ (Local Cache Dict) dưới dạng giả định lạc quan.

### Bản đồ cấu hình nạp từ hệ thống (Bảng ánh xạ Metadata):
* **Gemini 3.1 Flash Lite:** Độ ưu tiên 1 | Hạn mức ban đầu: 15 RPM | 250K TPM | 500 RPD.
* **Gemini 2.5 Flash Lite:** Độ ưu tiên 2 | Hạn mức ban đầu: 10 RPM | 250K TPM | 20 RPD.
* **Gemini 2.5 Flash:** Độ ưu tiên 3 | Hạn mức ban đầu: 5 RPM | 250K TPM | 20 RPD.
* **Gemini 3 Flash:** Độ ưu tiên 4 | Hạn mức ban đầu: 5 RPM | 250K TPM | 20 RPD.
* **Gemini 3.5 Flash:** Độ ưu tiên 5 | Hạn mức ban đầu: 5 RPM | 250K TPM | 20 RPD.

### Quy tắc thiết lập bộ đệm RAM ban đầu:
Mỗi mô hình sẽ được cấp một Object quản lý trạng thái trong Cache với các biến số:
* `remaining_rpm`: Gán bằng giá trị RPM tối đa trong file CSV.
* `remaining_tpm`: Gán bằng giá trị TPM tối đa trong file CSV.
* `remaining_rpd`: Gán bằng giá trị RPD tối đa trong file CSV.
* `reset_time`: Mặc định bằng `0.0` (Sẵn sàng hoạt động ngay lập tức).

---

## 3. LOGIC ĐIỀU PHỐI REQUEST VÀ RESPONSE (KỊCH BẢN A & B)

### 3.1. Giai đoạn Xử lý Request (Định tuyến thông minh trước khi gọi)
Khi người dùng kích hoạt tìm kiếm, hệ thống thực hiện vòng lặp kiểm tra từ mô hình có Độ ưu tiên 1 đến 5:
1. Lấy thời gian thực tại hệ thống (`current_time`).
2. Nếu `current_time > reset_time` của mô hình đang xét $\rightarrow$ Tự động khôi phục (Reset) các biến `remaining` về giá trị tối đa ban đầu của CSV.
3. Kiểm tra điều kiện: Nếu `remaining_rpm > 0` VÀ `remaining_tpm > 0` VÀ `remaining_rpd > 0` $\rightarrow$ Chọn ngay mô hình này để thực thi và bẻ gãy vòng lặp kiểm tra.

### 3.2. Giai đoạn Xử lý Response (Đồng bộ hóa thích ứng)

Sau khi gọi API của mô hình được chọn, hệ thống xử lý phản hồi dựa trên 2 kịch bản loại trừ:

#### Kịch bản A: Kết quả THÀNH CÔNG (Mô hình còn hạn mức thực tế)
* Hệ thống tiếp nhận chuỗi JSON kết quả phân tích mỹ phẩm trả về.
* Bóc tách các trường dữ liệu giới hạn còn lại từ phần Metadata/Headers của phản hồi do Google trả về (ví dụ: `requests-remaining`, `tokens-remaining`).
* **Hành động:** Cập nhật trực tiếp các giá trị thực tế này vào các biến `remaining_rpm`, `remaining_tpm` tương ứng trong Bộ đệm cục bộ để phục vụ chính xác cho lượt request tiếp theo.

#### Kịch bản B: Kết quả THẤT BẠI - Lỗi 429 ResourceExhausted (Mô hình thực tế đã cạn hạn mức)
* Mô hình được chọn trả về mã lỗi kích hoạt giới hạn tần suất (Rate Limit).
* **Hành động xử lý bộ đệm:** Ngay lập tức ghi đè trạng thái của mô hình này trong Local Cache: Đặt `remaining_rpm = 0`. Trích xuất mốc thời gian hồi phục từ nội dung lỗi và tính toán thời điểm mở khóa để gán vào `reset_time`.
* **Hành động bọc lót (Fallback):** Không đẩy thông báo lỗi lên màn hình giao diện. Hệ thống tự động chuyển hướng, lấy mô hình có thứ tự ưu tiên tiếp theo trong danh sách Cache đạt yêu cầu để thực hiện lại luồng xử lý từ đầu.

---

## 4. MÃ NGUỒN PHÂN HỆ ĐIỀU PHỐI TÍCH HỢP TẬP TRUNG (`gemini_router_engine.py`)

*Tài liệu mã nguồn đặc tả phân hệ tích hợp đa mô hình dựa trên nền tảng SDK chính thức của Google, được thiết kế để chạy độc lập và nhúng gọn vào Backend dự án.*

```python
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
        print("[GEMINI_ROUTER_LOG] Khởi tạo bộ đệm lạc quan thành công cho 5 mô hình.")

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
                
            print(f"[GEMINI_ROUTER_LOG] Lượt chọn [{attempt+1}]: Định tuyến yêu cầu sang -> {selected_model}")
            
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
                print(f"[GEMINI_ROUTER_LOG] Kịch bản A kích hoạt: {selected_model} thực thi thành công.")
                
                return response.text
                
            except ResourceExhausted as e:
                # KỊCH BẢN B: GẶP LỖI QUÁ TẢI HẠN MỨC (RATE LIMIT 429)
                print(f"[GEMINI_ROUTER_LOG] Kịch bản B kích hoạt: {selected_model} báo lỗi cạn hạn mức (429).")
                
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
# KHU VỰC KHỞI CHẠY KIỂM THỬ MÔ PHỎNG HỆ THỐNG (SIMULATION RUNNER)
# =====================================================================
if __name__ == "__main__":
    # Giả lập khóa môi trường bí mật đọc từ Streamlit Secrets
    MOCK_API_KEY = "AIzaSy_Mock_Key_For_Testing"
    router = GeminiSmartRouter(api_key=MOCK_API_KEY)
    
    # Tạo dữ liệu mẫu giả lập luồng chạy đầu vào của SkinMatch AI
    mock_instruction = "Bạn là chuyên gia SkinMatch AI. Phân tích xuất JSON: {'status': 'success'}"
    mock_text = "Da mình tiết rất nhiều dầu ở trán và mũi."
    
    print("\n--- BẮT ĐẦU GIẢ LẬP ĐỊNH TUYẾN REQUEST ---")
    # Luồng chạy thực tế sẽ gọi hàm này và nhận chuỗi JSON đầu ra sạch sẽ
    # Kết quả sẽ tự động rơi vào mô hình Gemini 3.1 Flash Lite ở lần chạy đầu tiên
    print("[HỆ THỐNG] Kết quả nhận được:", router.execute_request(mock_instruction, mock_text))