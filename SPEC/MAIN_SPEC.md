# TÀI LIỆU ĐẶC TẢ DỰ ÁN CHUẨN MASTER (PROJECT SPECIFICATION)
**Tên dự án:** Hệ thống Gợi ý Mỹ phẩm Thông minh tích hợp AI (SkinMatch AI)  
**Giai đoạn:** Prototype / MVP (Sản phẩm khả dụng tối thiểu)  
**Mô hình phát triển:** Tập trung và Đồng bộ (All-in-one Specification)  

---

## 1. HỆ SINH THÁI CÔNG NGHỆ & THÀNH PHẦN CỐT LÕI
Dự án được xây dựng hoàn toàn trên hệ sinh thái Python, ưu tiên tốc độ triển khai (Vibe Coding) và khả năng xử lý dữ liệu tích hợp tinh gọn không tách rời cấu phần API.

* **Ngôn ngữ lập trình chính:** `Python 3.x`
* **Framework Giao diện & Điều hướng:** `Streamlit` (Xây dựng UI tương tác hoàn toàn bằng Python, kiêm nhiệm luồng tiếp nhận Frontend và xử lý điều phối Backend).
* **Trí tuệ nhân tạo (AI Engine):** `Google Gemini API` (Sử dụng dòng mô hình tối ưu `gemini-1.5-flash` hỗ trợ xử lý Đa phương thức và ép kiểu cấu trúc JSON đầu ra).
* **Xử lý dữ liệu & Thuật toán nền:** `Pandas` (Rà quét, tính toán tập hợp và lọc dữ liệu trên tệp phẳng).
* **Xử lý hình ảnh:** Thư viện `Pillow (PIL)` (Đảm nhận xử lý nén dữ liệu Bytes thô từ client).
* **Quản lý cấu trúc dữ liệu:** `Pydantic` (Thiết lập Object Schema ràng buộc dữ liệu đầu ra của LLM).

---

## 2. KIẾN TRÚC DỮ LIỆU CƠ SỞ (DATA ARCHITECTURE)
Dữ liệu sản phẩm được lưu trữ ngầm dưới dạng file phẳng tối ưu tốc độ đọc nạp trực tiếp vào RAM của máy chủ lưu trữ.

* **Tệp CSDL Chính (Master Database):** `master_cosmetics_dataset.csv`
* **Quy mô:** 478 sản phẩm mỹ phẩm thương mại điện tử thực tế.
* **Cấu trúc trường thông tin (13 cột dữ liệu bắt buộc):**
    1.  `Product_Name`: Tên hiển thị của sản phẩm.
    2.  `Brand`: Thương hiệu chính xác của sản phẩm.
    3.  `Skin_Type`: Bộ nhãn loại da phù hợp (Lưu dạng chuỗi cách nhau bằng dấu phẩy).
    4.  `Skin_Concern`: Bộ nhãn vấn đề da giải quyết (Mụn, thâm, lão hóa, lỗ chân lông...).
    5.  `Texture`: Kết cấu của sản phẩm (Gel, bọt, bọt mịn, kem, nước...).
    6.  `Category`: Danh mục phân loại cứng (Sữa Rửa Mặt, Nước Tẩy Trang, Kem Chống Nắng).
    7.  `Product_Pic`: Link ảnh URL lưu trữ của sản phẩm (Dùng hiển thị UI).
    8.  `Product_URL`: Đường link gốc dẫn tới trang mua hàng.
    9.  `Description`: Đoạn văn bản mô tả gốc chứa tổng quan sản phẩm.
    10. `Uses`: Công dụng chi tiết phục vụ cho ngữ cảnh chấm điểm của AI.
    11. `Usage`: Hướng dẫn sử dụng gốc của nhà sản xuất.
    12. `Reviews`: Đánh giá ưu điểm nổi bật hỗ trợ tăng độ tin cậy khi gợi ý.
    13. `Price`: Định dạng số nguyên (`int64`), phục vụ tính năng kéo thanh giá và xử lý biên.

---

## 3. THIẾT KẾ GIAO DIỆN NGƯỜI DÙNG (FRONTEND DESIGN)
Giao diện Web App được chia bố cục không gian hai phần khoa học bằng Streamlit:

### 3.1. Thanh điều hướng bên trái (Sidebar Panel - Bộ lọc thủ công)
* **Bộ chọn Loại mỹ phẩm (Category):** Dạng Checkbox/Multiselect cho phép chọn nhiều đáp án cùng lúc (Sữa Rửa Mặt, Nước Tẩy Trang, Kem Chống Nắng).
* **Bộ chọn Loại da (Skin Type):** Cho phép tích chọn nhiều đặc tính (Da dầu, Da khô, Da nhạy cảm, Da hỗn hợp...).
* **Bộ chọn Tình trạng da (Skin Concern):** Cho phép tích chọn nhiều vấn đề (Mụn, Lỗ chân lông, Đỏ, Thâm...).
* **Thanh kéo giá tiền (Price Slider):** Cho phép điều chỉnh khoảng giá linh hoạt với giới hạn biên cứng từ **5.000đ** đến **1.500.000đ**.

### 3.2. Không gian hiển thị chính bên phải (Main Panel - Tiếp nhận AI & Kết quả)
* **Khung nhận diện Đa phương thức (Multimodal Input):**
    * Một ô nhập văn bản tự do (`st.text_area`) để người dùng kể về tình trạng da hiện tại.
    * Một nút tải ảnh lên (`st.file_uploader`) hỗ trợ người dùng gửi ảnh cận cảnh làn da hoặc nhãn chai mỹ phẩm cũ.
* **Nút kích hoạt tác vụ:** Nút bấm "Tìm kiếm / Tư vấn ngay".
* **Màn hình hiển thị:** Kết quả trả về dạng lưới (Grid) chứa Top 3 thẻ sản phẩm cá nhân hóa gồm: Ảnh bìa sản phẩm, Tên, Thương hiệu, Giá bán, Cách sử dụng cụ thể, và một đoạn văn phân tích khoa học lý do sản phẩm này tối ưu cho người dùng.

---

## 4. LOGIC XỬ LÝ NỀN BACKEND & CÁC QUY TẮC BIÊN GIỚI (EDGE CASES)
Để đảm bảo ứng dụng vận hành không lỗi mạng và an toàn tài nguyên, hệ thống áp dụng các quy tắc thiết kế logic sau:

### 4.1. Xử lý tệp hình ảnh dung lượng cao (Backend Auto-Compression)
* Khi người dùng tải lên ảnh độ phân giải cao (5MB - 10MB), Backend không gửi trực tiếp sang API để tránh trễ mạng học đường và sập RAM.
* Hệ thống dùng `Pillow` để can thiệp ngầm: Ép lại kích thước (Maximum Width 1024px) và giảm chất lượng nén xuống 70%. Bức ảnh co về mức dung lượng tối ưu (~200KB) trước khi truyền đi.

### 4.2. Logic xử lý xung đột bộ lọc (Hybrid OR Filter)
* Nếu có sự không đồng nhất giữa bộ lọc thủ công ở Sidebar (Ví dụ chọn: *Da khô*) và kết quả phân tích thị giác/văn bản từ Gemini (Ví dụ nhận diện: *Da dầu*), mã nguồn Pandas sẽ gộp hai tập hợp bằng toán tử `|` (OR).
* Hệ thống sẽ quét và hiển thị các sản phẩm phù hợp cho cả Da khô hoặc Da dầu nhằm mở rộng tối đa giải pháp cho khách hàng.

### 4.3. Logic xử lý bảng kết quả rỗng (Fallback Price Loosening)
* Nếu người dùng siết khoảng giá quá thấp ở Sidebar kết hợp chọn danh mục khiến bộ lọc thô ban đầu của Pandas trả về 0 sản phẩm thỏa mãn.
* Backend Python tự động kích hoạt hàm nới lỏng biên độ: Tăng giá trần bộ lọc lên thêm +20% so với vị trí thanh kéo của người dùng, tái lọc để luôn có ứng viên gửi sang cho mô hình AI xếp hạng.

### 4.4. Kiểm soát tính hợp lệ của Hình ảnh (Image Guardrails)
* Hệ thống cấu hình lớp chặn ảnh rác trực tiếp từ nhân xử lý của LLM. Nếu ảnh không hợp lệ, hệ thống ngắt tiến trình và hiển thị thông báo lỗi trực quan (`st.error`) ra màn hình Frontend.

### 4.5. Phạm vi xác thực người dùng (Auth Scope)
* **Giai đoạn 1 (Hiện tại):** Tạm hoãn tính năng Đăng nhập bằng Google và cơ sở dữ liệu tài khoản (Postponed to Post-MVP). Ứng dụng chạy ở chế độ Open-Access 100% miễn phí trên môi trường đám mây để tối ưu hóa tiến độ ra mắt.

---

## 5. CẤU PHẦN AI & KỸ THUẬT PROMPT ENGINEERING
Dự án áp dụng chiến lược **Tái Xếp Hạng Kết Quả (Pandas Pre-filtered Reranker)** để tối ưu chi phí Token và giảm thời gian phản hồi (Kiểm soát độ trễ lý tưởng từ 1.2s - 4s).

### 5.1. Định nghĩa Schema đầu ra bằng Pydantic
Mã nguồn ép cấu trúc đầu ra của Gemini API bắt buộc phải tuân theo cấu trúc JSON định sẵn (Structured Outputs), không chứa ký tự markdown thừa:
```python
class SkinMatchOutputSchema(BaseModel):
    is_valid_image: bool # Xác thực ảnh da hoặc nhãn mỹ phẩm
    error_code: Optional[str] # Trả về "invalid_image" nếu ảnh rác
    recommended_products: List[dict] # Chứa thông tin Top 3 sản phẩm gồm: Name, Pic, Price, Match_Reason, Usage