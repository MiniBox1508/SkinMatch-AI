import os
import sys
from dotenv import load_dotenv
from core.ai_engine import GeminiReranker
from core.gemini_router_engine import get_router_instance

# Force UTF-8 output for Windows console
sys.stdout.reconfigure(encoding='utf-8')

# Load biến môi trường
load_dotenv()

def test_router_connection():
    print("Bắt đầu bài kiểm tra kết nối API qua Gemini Smart Router...")
    
    # Khởi tạo Reranker (sẽ gọi Router bên dưới)
    api_key = os.getenv("AI_API_KEY")
    if not api_key or api_key == "INSERT_YOUR_GEMINI_API_KEY_HERE":
        print("Lỗi: Không tìm thấy cấu hình AI_API_KEY hợp lệ trong file .env")
        return

    reranker = GeminiReranker(api_key=api_key)
    
    # Trích xuất instance router để in trạng thái log
    router = get_router_instance(api_key)
    print("Danh sách ưu tiên mô hình hiện tại:")
    for m, cache in router.local_cache.items():
        print(f" - {m}: Priority {cache['priority']}, RPM {cache['remaining_rpm']}")
    
    # Mở ảnh thật từ EXAMPLE_IMAGE
    image_path = "EXAMPLE_IMAGE/Acne-vulgaris-body1.webp"
    print(f"\nĐang tải ảnh mẫu từ: {image_path}...")
    
    if not os.path.exists(image_path):
        print(f"❌ Không tìm thấy file ảnh: {image_path}")
        return
        
    print("Đang gửi Request tới hệ thống AI...")
    
    # Gửi thử nghiệm
    with open(image_path, "rb") as f:
        # Mock file object cho PIL Image.open
        from io import BytesIO
        img_byte_arr = BytesIO(f.read())
        
    result = reranker.generate_skin_match_native(
        user_text="Da tôi dạo này nổi rất nhiều nốt mụn sưng đỏ như trong hình, tôi nên làm gì?",
        uploaded_image=img_byte_arr,
        pandas_filtered_candidates_json='[]'
    )
    
    if not result:
        print("\n❌ Thất bại! Đã xảy ra lỗi khi gọi Model.")
        print("Bạn có thể kiểm tra lỗi chi tiết trong file 'error_logs.md'.")
    else:
        print("\n✅ Thành công! Kết nối Model không gặp lỗi nào.")
        print("Kết quả JSON trả về:")
        print(result)

if __name__ == "__main__":
    test_router_connection()
