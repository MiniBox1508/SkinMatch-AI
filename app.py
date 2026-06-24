import streamlit as st
import os
import json
from dotenv import load_dotenv
from core.data_processor import DataProcessor
from core.ai_engine import GeminiReranker

# Load biến môi trường (override=True để đảm bảo nạp key mới từ .env)
load_dotenv(override=True)

st.set_page_config(
    page_title="SkinMatch AI", 
    page_icon="✨", 
    layout="wide",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Custom CSS for premium aesthetics and responsiveness
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    
    /* Modern Card Design adapting to theme */
    .product-card {
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 24px;
        background: var(--background-color);
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        border: 1px solid var(--secondary-background-color);
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    .product-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        border-color: var(--primary-color);
    }
    
    /* Image container */
    .img-container {
        width: 100%;
        height: 220px;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        border-radius: 12px;
        margin-bottom: 20px;
        background-color: var(--secondary-background-color);
        padding: 10px;
    }
    .img-container img {
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
        transition: transform 0.3s ease;
    }
    .product-card:hover .img-container img {
        transform: scale(1.05);
    }
    
    .product-title {
        color: var(--text-color);
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 12px;
        line-height: 1.4;
    }
    
    .product-price {
        color: #e11d48;
        font-size: 1.4rem;
        font-weight: 800;
        margin-bottom: 20px;
        background: rgba(225, 29, 72, 0.1);
        padding: 6px 14px;
        border-radius: 10px;
        display: inline-block;
        border: 1px solid rgba(225, 29, 72, 0.2);
    }
    
    .product-reason {
        background: rgba(14, 165, 233, 0.1);
        padding: 16px;
        border-radius: 14px;
        border-left: 5px solid #0ea5e9;
        font-size: 0.95rem;
        margin-top: auto;
        color: var(--text-color);
        line-height: 1.6;
    }
    
    .product-usage {
        font-size: 0.9rem;
        color: var(--text-color);
        opacity: 0.9;
        margin-top: 16px;
        background: var(--secondary-background-color);
        padding: 14px;
        border-radius: 12px;
        border: 1px dashed var(--primary-color);
        line-height: 1.5;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 1rem 0 0.5rem 0;
        background: linear-gradient(to right, #4f46e5, #ec4899, #f59e0b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3rem;
        letter-spacing: -1px;
    }
    
    /* Subheader */
    .sub-header {
        text-align: center;
        color: var(--text-color);
        opacity: 0.8;
        font-size: 1.1rem;
        margin-bottom: 3rem;
        max-width: 600px;
        margin-left: auto;
        margin-right: auto;
        line-height: 1.5;
    }

    /* Tweak input areas for premium feel */
    .stTextArea textarea {
        border-radius: 12px;
        border: 1px solid var(--secondary-background-color);
        transition: all 0.3s;
    }
    .stTextArea textarea:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2);
    }
    
    /* Button */
    .stButton button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.3s !important;
    }
    /* Hide Streamlit default footer and deploy button ONLY */
    footer {visibility: hidden;}
    .stAppDeployButton {display: none !important;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">✨ SkinMatch AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Trợ lý bác sĩ da liễu cá nhân. Hãy mô tả vấn đề da hoặc tải ảnh lên, AI sẽ tìm ra những sản phẩm tối ưu nhất dành riêng cho bạn.</div>', unsafe_allow_html=True)

@st.cache_resource
def load_data():
    return DataProcessor("DATASET/master_cosmetics_dataset.csv")

processor = load_data()

# Lấy danh sách các thuộc tính để đưa vào Sidebar
categories = []
skin_types = []
skin_concerns = []

if not processor.df.empty:
    categories = processor.df['Category'].dropna().unique().tolist()
    
    # Extract unique skin types
    st_raw = processor.df['Skin_Type'].dropna().unique().tolist()
    st_set = set()
    for item in st_raw:
        for t in item.split(','):
            st_set.add(t.strip())
    skin_types = sorted(list(st_set))
    
    # Extract unique skin concerns
    sc_raw = processor.df['Skin_Concern'].dropna().unique().tolist()
    sc_set = set()
    for item in sc_raw:
        for c in item.split(','):
            sc_set.add(c.strip())
    skin_concerns = sorted(list(sc_set))
else:
    st.error("Không thể tải dataset. Vui lòng kiểm tra file `DATASET/master_cosmetics_dataset.csv`.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎯 Bộ lọc sản phẩm")
    st.markdown("Tinh chỉnh để kết quả chính xác hơn")
    
    selected_categories = st.multiselect("Danh mục mỹ phẩm", options=categories)
    selected_skin_types = st.multiselect("Loại da", options=skin_types)
    selected_skin_concerns = st.multiselect("Tình trạng da", options=skin_concerns)
    # Tạo danh sách mức giá có dấu chấm ngăn cách hàng nghìn
    price_options = [f"{i:,}".replace(",", ".") for i in range(5000, 1500001, 10000)]
    selected_price_labels = st.select_slider(
        "Khoảng giá (VNĐ)", 
        options=price_options, 
        value=(price_options[0], price_options[-1])
    )
    
    # Chuyển đổi chuỗi thành số nguyên để giữ nguyên logic lọc
    price_range = (
        int(selected_price_labels[0].replace(".", "")),
        int(selected_price_labels[1].replace(".", ""))
    )
    
    st.divider()
    st.header("⚙️ Cài đặt giao diện")
    
    # Theme and Toolbar selection logic
    import toml
    os.makedirs('.streamlit', exist_ok=True)
    config_path = '.streamlit/config.toml'
    
    try:
        with open(config_path, 'r') as f:
            config = toml.load(f)
    except Exception:
        config = {}
        
    needs_update = False
    
    # Ép Streamlit ẩn menu mặc định một cách chính thống (không dùng CSS để tránh lỗi mất nút sidebar)
    if 'client' not in config:
        config['client'] = {}
    if config['client'].get('toolbarMode') != 'minimal':
        config['client']['toolbarMode'] = 'minimal'
        needs_update = True
    
    current_theme = "Theo hệ thống"
    base = config.get('theme', {}).get('base', '')
    if base == 'light':
        current_theme = "Sáng"
    elif base == 'dark':
        current_theme = "Tối"

    theme_choice = st.radio("Chủ đề trang web", ["Theo hệ thống", "Sáng", "Tối"], index=["Theo hệ thống", "Sáng", "Tối"].index(current_theme))
    
    if theme_choice != current_theme:
        if 'theme' not in config:
            config['theme'] = {}
            
        if theme_choice == 'Sáng':
            config['theme']['base'] = 'light'
        elif theme_choice == 'Tối':
            config['theme']['base'] = 'dark'
        else:
            config['theme'].pop('base', None)
            
        needs_update = True
            
    if needs_update:
        with open(config_path, 'w') as f:
            toml.dump(config, f)
            
        # Dùng JavaScript ép trình duyệt tải lại ngay lập tức
        import streamlit.components.v1 as components
        components.html("<script>window.parent.location.reload();</script>", height=0)

# --- MAIN PANEL ---
# Sử dụng container để kiểm soát layout tốt hơn trên Mobile
input_container = st.container()

with input_container:
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("#### 📝 Mô tả tình trạng da")
        user_text = st.text_area("Bạn đang gặp vấn đề gì? Da bạn cần cấp ẩm, trị mụn hay dưỡng trắng?", height=160, label_visibility="collapsed", placeholder="Ví dụ: Dạo này da tôi đổ nhiều dầu vùng chữ T và có mụn sưng viêm ở trán...")

    with col2:
        st.markdown("#### 📸 Hình ảnh đính kèm (Tùy chọn)")
        uploaded_image = st.file_uploader("Tải lên ảnh da mặt hoặc nhãn mỹ phẩm", type=["jpg", "jpeg", "png", "webp", "bmp", "tiff"], label_visibility="collapsed")

st.write("") # Spacing
submit_button = st.button("🚀 TÌM KIẾM SẢN PHẨM PHÙ HỢP", type="primary", use_container_width=True)
st.write("") # Spacing

if submit_button:
    # 1. Load environment variables
    load_dotenv()
    api_key = os.getenv("AI_API_KEY")

    # Check for API key (but allow the app to run and show a warning)
    if not api_key:
        # Nếu không có file .env, thử đọc từ file secrets.toml của Streamlit Cloud
        try:
            api_key = st.secrets.get("AI_API_KEY")
        except Exception:
            api_key = None
            
    if not api_key:
        st.error("Hệ thống chưa được cấu hình AI API Key trong file .env hoặc secrets.toml")
        st.stop()
        
    if not user_text.strip() and not uploaded_image:
        st.warning("Vui lòng nhập mô tả hoặc tải hình ảnh lên để AI có dữ liệu phân tích.")
        st.stop()
        
    with st.spinner("Đang sàng lọc dữ liệu nền..."):
        # 2. Lọc bằng Pandas
        min_price, max_price = price_range
        candidates = processor.filter_candidates(
            categories=selected_categories,
            skin_types=selected_skin_types,
            skin_concerns=selected_skin_concerns,
            min_price=min_price,
            max_price=max_price
        )
        
        if not candidates:
            st.error("Không tìm thấy sản phẩm nào phù hợp với bộ lọc (kể cả sau khi đã nới lỏng ngân sách). Vui lòng thử mở rộng tiêu chí.")
            st.stop()
            
        candidates_json = processor.get_candidates_json(candidates)
        
    with st.spinner("✨ SkinMatch AI đang phân tích hình ảnh và tìm kiếm sản phẩm phù hợp..."):
        # 3. Gọi Gemini
        reranker = GeminiReranker(api_key=api_key)
        result_text = reranker.generate_skin_match_native(
            user_text=user_text,
            uploaded_image=uploaded_image,
            pandas_filtered_candidates_json=candidates_json
        )
        
        if result_text:
            try:
                result_data = json.loads(result_text)
                
                # Xử lý trường hợp ảnh rác
                if not result_data.get('is_valid_image', True):
                    st.error(f"❌ **Phát hiện hình ảnh không hợp lệ** (Mã lỗi: `{result_data.get('error_code', 'unknown')}`).\nHệ thống AI đánh giá ảnh tải lên không chứa bề mặt da người hoặc nhãn mỹ phẩm. Vui lòng tải lên ảnh đúng chuẩn.")
                    st.stop()
                    
                recommended = result_data.get('recommended_products', [])
                
                if not recommended:
                    st.warning("AI không tìm thấy sản phẩm nào thực sự thỏa mãn các tiêu chí y khoa nghiêm ngặt trong danh sách ứng viên hiện tại.")
                else:
                    st.success(f"🎉 Tuyệt vời! AI đã phân tích và tìm ra **{len(recommended)} sản phẩm** phù hợp nhất dành riêng cho bạn.")
                    st.write("")
                    
                    # Hiển thị dạng Grid responsive
                    cols = st.columns(min(len(recommended), 3), gap="large")
                    for i, prod in enumerate(recommended[:3]): # Top 3
                        with cols[i]:
                            pic_url = prod.get('Product_Pic', '')
                            img_html = f'<div class="img-container"><img src="{pic_url}" alt="Product Image"></div>' if pic_url else ''
                            
                            price = prod.get('Price', 0)
                            formatted_price = f"{price:,} VNĐ" if price else "Đang cập nhật"
                            
                            product_url = prod.get('Product_URL', '#')
                            st.markdown(f'''
                            <div class="product-card">
                                {img_html}
                                <div class="product-title">{prod.get("Product_Name", "N/A")}</div>
                                <div class="product-price">{formatted_price}</div>
                                <div class="product-reason">
                                    <strong>💡 Tại sao sản phẩm này phù hợp?</strong><br/>
                                    {prod.get("Match_Reason", "")}
                                </div>
                                <div class="product-usage">
                                    <strong>📝 Hướng dẫn sử dụng:</strong><br/>
                                    {prod.get("Usage", "")}
                                </div>
                                <a href="{product_url}" target="_blank" style="display: block; text-align: center; margin-top: 15px; padding: 10px; background-color: #ff4b4b; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">Xem chi tiết sản phẩm</a>
                            </div>
                            ''', unsafe_allow_html=True)
                            
            except json.JSONDecodeError:
                st.error("Lỗi phân tích cú pháp kết quả từ AI. Định dạng JSON không hợp lệ.")
                st.write(result_text)
        else:
            st.error("Đã xảy ra lỗi khi kết nối với hệ thống AI.")
