# WORKFLOW VÀ BÁO CÁO DI TRÚ NATIVE SDK (GROK-4.3 -> GEMINI 2.5 FLASH LITE)

**Dự án:** Hệ thống Gợi ý Mỹ phẩm Thông minh (SkinMatch AI)  
**Kịch bản chuyển đổi:** Kịch bản 2 - Chuyển hẳn về SDK chính thức của Google (Native Connection)  
**Nguyên tắc codebase:** Chỉ can thiệp vào các tệp cấu hình, cấu trúc hàm gọi API, tên tệp kiểm thử, tên hàm và nhãn logs liên quan trực tiếp đến AI Engine. Tuyệt đối giữ nguyên vẹn giao diện Streamlit, logic xử lý tệp phẳng và bộ lọc dữ liệu của Pandas.

---

## 1. BÁO CÁO CÁC THÀNH PHẦN ĐÃ CHỈNH SỬA VÀ QUY HOẠCH

Để hệ thống chuyển từ cơ chế gọi của Grok (OpenAI Client) sang cơ chế chạy trực tiếp của Google AI Studio, các thành phần sau đã được thay đổi cục bộ:

1. **Tệp cấu hình (`secrets.toml`):** Gỡ bỏ hoàn toàn trường `AI_BASE_URL` (do SDK của Google tự động định tuyến đến máy chủ chính chủ). Giữ lại `AI_API_KEY` và cập nhật mã định danh mô hình tại `AI_MODEL_NAME`.
2. **Tệp môi trường (`requirements.txt`):** Gỡ bỏ thư viện `openai` nếu không còn sử dụng cho tác vụ khác, bổ sung thư viện native chính thức của Google: `google-generativeai`.
3. **Hệ thống tên hàm (Function Nomenclature):** Đổi tên hàm điều phối chính tại Backend từ `call_multimodal_skin_ai` (kiểu cũ của Grok) thành `generate_skin_match_native` (kiểu mới của Gemini).
4. **Hệ thống Nhật ký (Logs System):** Đổi toàn bộ ký hiệu nhật ký hiển thị tại terminal hệ thống từ `[GROK_4.3_LOG]` thành `[GEMINI_2.5_LITE_LOG]`.
5. **Dọn dẹp và Tái lập phân hệ Kiểm thử:**
   * **XÓA THƯ MỤC/FILE CŨ:** Tiến hành xóa bỏ hoàn toàn file test đa phương thức cũ của Grok (`test_grok_multimodal.py`).
   * **TẠO FILE MỚI:** Khởi tạo file test native độc lập mới với tên gọi `test_gemini_multimodal.py` để xử lý dữ liệu text kết hợp tệp ảnh mẫu có tên `EXAMPLE_IMAGE`.

---

## 2. CHI TIẾT WORKFLOW THỰC HIỆN (STEP-BY-STEP WORKFLOW)

### Bước 2.1: Đồng bộ hóa cấu hình môi trường mới
Cập nhật phân hệ quản lý biến môi trường tại `.streamlit/secrets.toml` (hoặc mục Streamlit Cloud Secrets):

```toml
# Gỡ bỏ đường dẫn URL cũ của OpenRouter/xAI, cấu hình chuẩn Native Google
AI_API_KEY = "MÃ_KHÓA_API_KEY_MỚI_LẤY_TỪ_GOOGLE_AI_STUDIO"
AI_MODEL_NAME = "gemini-2.5-flash-lite"