"""
Hệ Thống Chuyển Văn Bản Thành Giọng Nói AI (Edge-TTS)
------------------------------------------------------
Ứng dụng Streamlit tạo giọng đọc AI tự động đa chủ đề, sử dụng thư viện
`edge-tts` (Microsoft Edge Text-to-Speech) - MIỄN PHÍ 100%, KHÔNG CẦN API KEY.

Chạy ứng dụng:
    streamlit run app.py
"""

import asyncio
import io
import re
from datetime import datetime

import edge_tts
import streamlit as st
from pydub import AudioSegment

# =====================================================================================
# 1. CẤU HÌNH TRANG (PAGE CONFIG)
# =====================================================================================
st.set_page_config(
    page_title="Trình Tạo Giọng Đọc AI Đa Chủ Đề",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================================================
# 2. DANH MỤC GIỌNG ĐỌC (VOICE DICT)
# =====================================================================================
# Key: Tên hiển thị trên giao diện | Value: (voice_id, mô tả ngắn)
VOICES = {
    # ---- Tiếng Việt (2 giọng chính thức duy nhất mà Edge-TTS hỗ trợ) ----
    "🇻🇳 Nam Minh - Nam (Miền Bắc)": {
        "id": "vi-VN-NamMinhNeural",
        "desc": "Giọng nam miền Bắc, trầm ấm, chuẩn mực. Phù hợp: Bản tin, Bất động sản, Doanh nghiệp.",
    },
    "🇻🇳 Hoài My - Nữ (Miền Bắc)": {
        "id": "vi-VN-HoaiMyNeural",
        "desc": "Giọng nữ miền Bắc, truyền cảm, nhẹ nhàng. Phù hợp: Phóng sự, Review, Storytelling.",
    },
    # ---- Tiếng Anh - Mỹ (US English) ----
    "🇺🇸 Jenny - Nữ, thân thiện": {
        "id": "en-US-JennyNeural",
        "desc": "Giọng nữ tiếng Anh Mỹ chuẩn, tự nhiên, thân thiện. Phù hợp: Nội dung chung, E-learning.",
    },
    "🇺🇸 Guy - Nam, mạnh mẽ": {
        "id": "en-US-GuyNeural",
        "desc": "Giọng nam tiếng Anh Mỹ, rõ ràng, mạnh mẽ. Phù hợp: Thuyết trình, Quảng cáo.",
    },
    "🇺🇸 Aria - Nữ, ấm áp đa năng": {
        "id": "en-US-AriaNeural",
        "desc": "Giọng nữ tiếng Anh Mỹ ấm áp, biểu cảm tự nhiên. Phù hợp: Review, Storytelling, Quảng cáo.",
    },
    "🇺🇸 Christopher - Nam, trầm ổn trọng": {
        "id": "en-US-ChristopherNeural",
        "desc": "Giọng nam trầm, uy tín, đáng tin cậy. Phù hợp: Tin tức, Doanh nghiệp, Giáo dục.",
    },
    "🇺🇸 Eric - Nam, điềm đạm rõ ràng": {
        "id": "en-US-EricNeural",
        "desc": "Giọng nam điềm đạm, phát âm rõ ràng. Phù hợp: E-learning, Hướng dẫn, Tutorial.",
    },
    "🇺🇸 Michelle - Nữ, chuyên nghiệp": {
        "id": "en-US-MichelleNeural",
        "desc": "Giọng nữ chuyên nghiệp, sắc sảo. Phù hợp: Doanh nghiệp, Thuyết trình, Tin tức.",
    },
    "🇺🇸 Roger - Nam, ấm áp từng trải": {
        "id": "en-US-RogerNeural",
        "desc": "Giọng nam lớn tuổi hơn, ấm áp, từng trải. Phù hợp: Kể chuyện, Audiobook, Podcast.",
    },
    "🇺🇸 Ana - Nữ, giọng trẻ em": {
        "id": "en-US-AnaNeural",
        "desc": "Giọng bé gái trong trẻo. Phù hợp: Nội dung thiếu nhi, Giáo dục mầm non.",
    },
    "🇺🇸 Andrew (Multilingual) - Nam, tự nhiên": {
        "id": "en-US-AndrewMultilingualNeural",
        "desc": "Giọng nam đa ngôn ngữ, tự nhiên như hội thoại đời thực. Phù hợp: Podcast, MC sự kiện, Kể chuyện.",
    },
    "🇺🇸 Ava (Multilingual) - Nữ, biểu cảm": {
        "id": "en-US-AvaMultilingualNeural",
        "desc": "Giọng nữ đa ngôn ngữ, biểu cảm sống động. Phù hợp: Quảng cáo, Review, Nội dung sáng tạo.",
    },
    # ---- Tiếng Anh - Anh (UK English) ----
    "🇬🇧 Sonia - Nữ, thanh lịch Anh-Anh": {
        "id": "en-GB-SoniaNeural",
        "desc": "Giọng nữ Anh-Anh thanh lịch, sang trọng. Phù hợp: Bất động sản cao cấp, Quảng cáo premium.",
    },
    "🇬🇧 Ryan - Nam, lịch lãm Anh-Anh": {
        "id": "en-GB-RyanNeural",
        "desc": "Giọng nam Anh-Anh lịch lãm, chững chạc. Phù hợp: Doanh nghiệp, MC sự kiện, Quảng cáo premium.",
    },
}

# Danh sách giọng tiếng Việt - hiển thị mặc định, ưu tiên hàng đầu trên giao diện.
# Microsoft/Edge-TTS hiện CHỈ phát hành chính thức 2 giọng tiếng Việt (đã kiểm chứng qua
# danh sách giọng thực tế của thư viện edge-tts): vi-VN-NamMinhNeural (nam) và
# vi-VN-HoaiMyNeural (nữ). Đây là giới hạn từ phía Microsoft, ứng dụng không thể tự thêm
# giọng Việt thứ 3 - nếu Microsoft phát hành thêm, chỉ cần thêm vào dict VOICES phía trên.
VN_VOICE_KEYS = [k for k in VOICES if k.startswith("🇻🇳")]
FOREIGN_VOICE_KEYS = [k for k in VOICES if not k.startswith("🇻🇳")]

# =====================================================================================
# 3. KHO KỊCH BẢN MẪU THEO CHỦ ĐỀ x VÙNG MIỀN (TEMPLATES SELECTOR)
# =====================================================================================
# Lưu ý: Edge-TTS chỉ cung cấp 2 giọng tiếng Việt (Nam Minh, Hoài My - đều là giọng
# chuẩn miền Bắc), Microsoft chưa có giọng đọc riêng theo phương ngữ từng vùng miền.
# Vì vậy phần "vùng miền" dưới đây tùy biến NỘI DUNG kịch bản (địa danh, sông, thành
# phố...) theo từng địa phương, còn giọng đọc vẫn chọn ở mục Cấu Hình Giọng Đọc.

TOPIC_OPTIONS = [
    "🏢 Bất Động Sản (Sang trọng / Thôi thúc)",
    "📰 Tin Tức / Phóng Sự",
    "📖 Review / Kể Chuyện",
    "📢 Quảng Cáo / Giới Thiệu Sản Phẩm",
    "🎓 Giáo Dục / E-Learning",
    "🎧 Podcast / Truyện Audio",
    "💍 MC Sự Kiện / Đám Cưới",
    "✍️ Tự nhập văn bản tự do",
]

# Thông tin đặc trưng của từng vùng miền, dùng để dựng kịch bản
REGIONS = {
    "Nghệ An (TP Vinh)": {"noun_phrase": "thành phố Vinh, xứ Nghệ", "landmark": "sông Lam"},
    "Huế (Cố đô)": {"noun_phrase": "cố đô Huế nghìn năm văn hiến", "landmark": "sông Hương"},
    "Đà Nẵng": {"noun_phrase": "thành phố đáng sống Đà Nẵng", "landmark": "sông Hàn"},
    "Hà Nội": {"noun_phrase": "thủ đô Hà Nội ngàn năm văn hiến", "landmark": "sông Hồng"},
    "TP. Hồ Chí Minh": {"noun_phrase": "thành phố Hồ Chí Minh năng động", "landmark": "sông Sài Gòn"},
}

# Kịch bản biên soạn riêng, chi tiết cho 2 vùng miền trọng tâm: Nghệ An & Huế
CURATED_SCRIPTS = {
    ("🏢 Bất Động Sản (Sang trọng / Thôi thúc)", "Nghệ An (TP Vinh)"): (
        "Tọa lạc tại vị trí đắc địa bậc nhất thành phố Vinh, dự án khu đô thị mới "
        "do Sun Group phát triển tự hào mang đến một chuẩn sống thượng lưu chưa từng có "
        "tại xứ Nghệ.\n\n"
        "Không chỉ là nơi an cư, đây còn là biểu tượng phồn vinh mới - nơi hội tụ trọn vẹn "
        "hệ sinh thái tiện ích đẳng cấp quốc tế: quảng trường ánh sáng, phố đi bộ thương mại, "
        "công viên trung tâm, trường học liên cấp và bệnh viện quốc tế, tất cả trong tầm tay "
        "cư dân.\n\n"
        "Với thiết kế kiến trúc tân cổ điển sang trọng, cùng chính sách bán hàng ưu đãi vượt trội "
        "dành riêng cho một trăm khách hàng đầu tiên, đây chính là cơ hội đầu tư vàng không thể "
        "bỏ lỡ trong năm nay.\n\n"
        "Cơ hội sở hữu bất động sản triệu đô đang đến rất gần. Quý khách hàng vui lòng liên hệ "
        "ngay hotline, hoặc Zalo không không chín bảy bảy, sáu tám bảy, hai hai bảy để được tư vấn "
        "và giữ chỗ thiện đầu tiên. Số không chín bảy bảy chấm sáu tám bảy chấm hai hai bảy - "
        "cơ hội chỉ dành cho những khách hàng nhanh tay nhất."
    ),
    ("🏢 Bất Động Sản (Sang trọng / Thôi thúc)", "Huế (Cố đô)"): (
        "Tọa lạc bên dòng sông Hương thơ mộng, ngay giữa lòng cố đô Huế nghìn năm văn hiến, "
        "dự án khu đô thị ven sông tự hào kiến tạo một chuẩn sống an nhiên, sang trọng bậc nhất "
        "miền Trung.\n\n"
        "Không chỉ là chốn an cư, đây còn là không gian sống di sản đương đại - nơi hội tụ công "
        "viên cảnh quan ven sông, phố đi bộ ẩm thực cung đình, quảng trường văn hóa và hệ thống "
        "tiện ích nghỉ dưỡng chuẩn năm sao, tất cả trong tầm tay cư dân.\n\n"
        "Với thiết kế kiến trúc pha trộn tinh hoa cung đình Huế và phong cách hiện đại, cùng chính "
        "sách ưu đãi đặc biệt dành riêng cho những khách hàng đặt chỗ sớm nhất, đây chính là cơ hội "
        "đầu tư hiếm có giữa lòng cố đô.\n\n"
        "Cơ hội sở hữu bất động sản ven sông Hương đang đến rất gần. Quý khách hàng vui lòng liên hệ "
        "ngay hotline, hoặc Zalo không không chín bảy bảy, sáu tám bảy, hai hai bảy để được tư vấn "
        "và giữ chỗ sớm nhất. Số không chín bảy bảy chấm sáu tám bảy chấm hai hai bảy - cơ hội chỉ "
        "dành cho những khách hàng nhanh tay nhất."
    ),
    ("📰 Tin Tức / Phóng Sự", "Nghệ An (TP Vinh)"): (
        "Bản tin chuyển động đô thị hôm nay xin gửi tới quý vị và các bạn những thông tin nổi bật "
        "về tốc độ phát triển hạ tầng tại tỉnh Nghệ An.\n\n"
        "Trong những năm gần đây, thành phố Vinh đang chuyển mình mạnh mẽ để trở thành trung tâm "
        "kinh tế, văn hóa của khu vực Bắc Trung Bộ. Hàng loạt tuyến đường huyết mạch được mở rộng, "
        "nhiều khu đô thị mới quy mô lớn lần lượt được khởi công, kéo theo làn sóng dịch chuyển dân cư "
        "và dòng vốn đầu tư đổ về ngày càng mạnh mẽ.\n\n"
        "Theo đánh giá của giới chuyên gia, quy hoạch mở rộng địa giới hành chính cùng với sự xuất hiện "
        "của các nhà đầu tư chiến lược đã và đang tạo ra một diện mạo hoàn toàn mới cho đô thị Vinh, "
        "hứa hẹn đưa thành phố trở thành điểm sáng đáng sống bậc nhất miền Trung trong thập kỷ tới.\n\n"
        "Chương trình chuyển động đô thị đến đây xin tạm dừng. Xin kính chào và hẹn gặp lại quý vị "
        "trong những bản tin tiếp theo."
    ),
    ("📰 Tin Tức / Phóng Sự", "Huế (Cố đô)"): (
        "Bản tin chuyển động đô thị hôm nay xin gửi tới quý vị và các bạn những thông tin nổi bật "
        "về tốc độ phát triển hạ tầng tại thành phố Huế.\n\n"
        "Trong những năm gần đây, cố đô Huế đang chuyển mình mạnh mẽ để trở thành đô thị di sản, "
        "văn hóa và du lịch đặc trưng của cả nước. Hàng loạt tuyến đường ven sông Hương được chỉnh "
        "trang, nhiều khu đô thị mới quy mô lớn lần lượt được khởi công, kéo theo làn sóng dịch chuyển "
        "dân cư và dòng vốn đầu tư đổ về ngày càng mạnh mẽ.\n\n"
        "Theo đánh giá của giới chuyên gia, việc Huế trở thành thành phố trực thuộc Trung ương cùng "
        "với chiến lược bảo tồn gắn liền với phát triển đã và đang tạo ra một diện mạo hoàn toàn mới "
        "cho đô thị cố đô, hứa hẹn đưa Huế trở thành điểm sáng đáng sống bậc nhất miền Trung trong "
        "thập kỷ tới.\n\n"
        "Chương trình chuyển động đô thị đến đây xin tạm dừng. Xin kính chào và hẹn gặp lại quý vị "
        "trong những bản tin tiếp theo."
    ),
    ("📖 Review / Kể Chuyện", "Nghệ An (TP Vinh)"): (
        "Có một buổi chiều, tôi tình cờ ghé qua khu dân cư ven sông Lam, và cảm giác đầu tiên khi "
        "bước chân xuống xe là một sự bình yên đến lạ.\n\n"
        "Gió từ sông thổi vào mát rượi, xa xa là hàng cây xanh rợp bóng chạy dọc theo bờ kè, tiếng "
        "trẻ con nô đùa trong công viên nội khu hòa cùng tiếng chim hót khiến tôi bất giác mỉm cười. "
        "Không gian sống nơi đây thực sự khác biệt so với sự ồn ào, ngột ngạt của phố thị mà tôi vẫn "
        "quen thuộc mỗi ngày.\n\n"
        "Ngồi nhâm nhi ly cà phê tại quán ven sông, ngắm hoàng hôn buông xuống mặt nước lấp lánh, tôi "
        "chợt nhận ra đây chính xác là hình ảnh chốn an cư mà bao người vẫn hằng mơ ước - nơi con người "
        "được sống chậm lại, gần gũi với thiên nhiên nhưng vẫn không xa rời tiện nghi hiện đại.\n\n"
        "Nếu bạn cũng đang tìm kiếm một nơi để trở về sau ngày dài mệt mỏi, tôi nghĩ khu đô thị ven "
        "sông Lam này rất xứng đáng để bạn dành thời gian ghé thăm và trải nghiệm."
    ),
    ("📖 Review / Kể Chuyện", "Huế (Cố đô)"): (
        "Có một buổi chiều, tôi tình cờ ghé qua khu dân cư ven sông Hương, và cảm giác đầu tiên khi "
        "bước chân xuống xe là một sự tĩnh tại đến lạ.\n\n"
        "Gió từ sông thổi vào mát rượi, xa xa là những nhịp cầu bắc qua dòng Hương giang, tiếng "
        "chuông chùa vọng lại từ xa hòa cùng tiếng đò dọc sông khiến tôi bất giác chậm lại. Không "
        "gian sống nơi đây mang một vẻ đẹp trầm mặc, sâu lắng rất riêng của xứ Huế mộng mơ.\n\n"
        "Ngồi nhâm nhi ly trà sen bên hiên nhà ven sông, ngắm hoàng hôn buông xuống mặt nước lấp "
        "lánh, tôi chợt nhận ra đây chính xác là hình ảnh chốn an cư mà bao người vẫn hằng mơ ước - "
        "nơi con người được sống chậm lại, gần gũi với văn hóa cố đô nhưng vẫn không xa rời tiện "
        "nghi hiện đại.\n\n"
        "Nếu bạn cũng đang tìm kiếm một nơi để trở về sau ngày dài mệt mỏi, tôi nghĩ khu đô thị ven "
        "sông Hương này rất xứng đáng để bạn dành thời gian ghé thăm và trải nghiệm."
    ),
    ("📢 Quảng Cáo / Giới Thiệu Sản Phẩm", "Nghệ An (TP Vinh)"): (
        "Bạn đang tìm kiếm một sản phẩm chất lượng, được hàng ngàn khách hàng tin dùng tại thành "
        "phố Vinh? Xin giới thiệu đến quý khách bộ sản phẩm mới nhất, được nghiên cứu và phát triển "
        "dành riêng cho người tiêu dùng xứ Nghệ.\n\n"
        "Với chất lượng vượt trội, thiết kế tinh tế cùng mức giá vô cùng hợp lý, sản phẩm của chúng "
        "tôi cam kết mang đến sự hài lòng tuyệt đối ngay từ lần sử dụng đầu tiên.\n\n"
        "Nhân dịp khai trương chi nhánh mới tại thành phố Vinh, chúng tôi dành tặng ưu đãi giảm giá "
        "đặc biệt lên đến ba mươi phần trăm cho một trăm khách hàng đặt mua sớm nhất.\n\n"
        "Đừng bỏ lỡ cơ hội này! Quý khách vui lòng liên hệ ngay hotline, hoặc Zalo không không chín "
        "bảy bảy, sáu tám bảy, hai hai bảy để được tư vấn miễn phí và nhận ưu đãi ngay hôm nay."
    ),
    ("📢 Quảng Cáo / Giới Thiệu Sản Phẩm", "Huế (Cố đô)"): (
        "Bạn đang tìm kiếm một sản phẩm chất lượng, được hàng ngàn khách hàng tin dùng tại cố đô "
        "Huế? Xin giới thiệu đến quý khách bộ sản phẩm mới nhất, được nghiên cứu và phát triển dành "
        "riêng cho người tiêu dùng xứ Huế.\n\n"
        "Với chất lượng vượt trội, thiết kế tinh tế cùng mức giá vô cùng hợp lý, sản phẩm của chúng "
        "tôi cam kết mang đến sự hài lòng tuyệt đối ngay từ lần sử dụng đầu tiên.\n\n"
        "Nhân dịp khai trương chi nhánh mới tại thành phố Huế, chúng tôi dành tặng ưu đãi giảm giá "
        "đặc biệt lên đến ba mươi phần trăm cho một trăm khách hàng đặt mua sớm nhất.\n\n"
        "Đừng bỏ lỡ cơ hội này! Quý khách vui lòng liên hệ ngay hotline, hoặc Zalo không không chín "
        "bảy bảy, sáu tám bảy, hai hai bảy để được tư vấn miễn phí và nhận ưu đãi ngay hôm nay."
    ),
    ("🎓 Giáo Dục / E-Learning", "Nghệ An (TP Vinh)"): (
        "Chào mừng các bạn học viên đã đến với bài học hôm nay, được thực hiện bởi đội ngũ giảng "
        "viên giàu kinh nghiệm tại trung tâm đào tạo thành phố Vinh.\n\n"
        "Trong bài học này, chúng ta sẽ cùng nhau tìm hiểu những kiến thức nền tảng quan trọng, được "
        "trình bày một cách dễ hiểu, có ví dụ minh họa cụ thể, giúp các bạn nắm vững nội dung chỉ sau "
        "một buổi học.\n\n"
        "Hãy chuẩn bị giấy bút, tập trung theo dõi bài giảng, và đừng ngần ngại ghi lại những câu "
        "hỏi để chúng ta cùng thảo luận ở phần cuối bài học.\n\n"
        "Bây giờ, chúng ta hãy cùng bắt đầu bài học đầu tiên nhé!"
    ),
    ("🎓 Giáo Dục / E-Learning", "Huế (Cố đô)"): (
        "Chào mừng các bạn học viên đã đến với bài học hôm nay, được thực hiện bởi đội ngũ giảng "
        "viên giàu kinh nghiệm tại trung tâm đào tạo thành phố Huế.\n\n"
        "Trong bài học này, chúng ta sẽ cùng nhau tìm hiểu những kiến thức nền tảng quan trọng, được "
        "trình bày một cách dễ hiểu, có ví dụ minh họa cụ thể, giúp các bạn nắm vững nội dung chỉ sau "
        "một buổi học.\n\n"
        "Hãy chuẩn bị giấy bút, tập trung theo dõi bài giảng, và đừng ngần ngại ghi lại những câu "
        "hỏi để chúng ta cùng thảo luận ở phần cuối bài học.\n\n"
        "Bây giờ, chúng ta hãy cùng bắt đầu bài học đầu tiên nhé!"
    ),
    ("🎧 Podcast / Truyện Audio", "Nghệ An (TP Vinh)"): (
        "Xin chào tất cả các bạn, chào mừng các bạn đã quay trở lại với podcast của chúng tôi, nơi "
        "mỗi tuần chúng ta cùng nhau trò chuyện về những câu chuyện đời thường thật gần gũi.\n\n"
        "Số phát sóng hôm nay, mình muốn kể cho các bạn nghe về một buổi chiều lang thang dọc bờ "
        "sông Lam, thành phố Vinh - nơi mình tình cờ gặp gỡ những con người bình dị nhưng mang trong "
        "mình biết bao câu chuyện thú vị.\n\n"
        "Nếu các bạn cũng có những kỷ niệm đáng nhớ về mảnh đất xứ Nghệ, đừng ngần ngại để lại bình "
        "luận, mình rất mong được lắng nghe câu chuyện của các bạn.\n\n"
        "Cảm ơn các bạn đã lắng nghe, hẹn gặp lại trong số phát sóng tuần sau!"
    ),
    ("🎧 Podcast / Truyện Audio", "Huế (Cố đô)"): (
        "Xin chào tất cả các bạn, chào mừng các bạn đã quay trở lại với podcast của chúng tôi, nơi "
        "mỗi tuần chúng ta cùng nhau trò chuyện về những câu chuyện đời thường thật gần gũi.\n\n"
        "Số phát sóng hôm nay, mình muốn kể cho các bạn nghe về một buổi chiều lang thang dọc bờ "
        "sông Hương, cố đô Huế - nơi mình tình cờ gặp gỡ những con người bình dị nhưng mang trong "
        "mình biết bao câu chuyện thú vị.\n\n"
        "Nếu các bạn cũng có những kỷ niệm đáng nhớ về mảnh đất xứ Huế mộng mơ, đừng ngần ngại để "
        "lại bình luận, mình rất mong được lắng nghe câu chuyện của các bạn.\n\n"
        "Cảm ơn các bạn đã lắng nghe, hẹn gặp lại trong số phát sóng tuần sau!"
    ),
    ("💍 MC Sự Kiện / Đám Cưới", "Nghệ An (TP Vinh)"): (
        "Kính thưa quý vị quan khách, cô dâu chú rể cùng toàn thể gia đình hai họ! Trong không khí "
        "ấm áp và hạnh phúc tại thành phố Vinh hôm nay, chúng ta cùng nhau hội tụ để chứng kiến "
        "khoảnh khắc thiêng liêng - lễ thành hôn của đôi uyên ương.\n\n"
        "Xin một tràng pháo tay thật lớn để chào đón sự xuất hiện của cô dâu và chú rể trong ngày "
        "trọng đại nhất cuộc đời!\n\n"
        "Tình yêu của hai bạn đã vượt qua bao thử thách để đơm hoa kết trái, và hôm nay, trước sự "
        "chứng kiến của gia đình, bạn bè, hai bạn chính thức về chung một nhà.\n\n"
        "Xin chúc cô dâu chú rể trăm năm hạnh phúc, bạc đầu răng long, sớm sinh quý tử!"
    ),
    ("💍 MC Sự Kiện / Đám Cưới", "Huế (Cố đô)"): (
        "Kính thưa quý vị quan khách, cô dâu chú rể cùng toàn thể gia đình hai họ! Trong không khí "
        "ấm áp và hạnh phúc giữa lòng cố đô Huế hôm nay, chúng ta cùng nhau hội tụ để chứng kiến "
        "khoảnh khắc thiêng liêng - lễ thành hôn của đôi uyên ương.\n\n"
        "Xin một tràng pháo tay thật lớn để chào đón sự xuất hiện của cô dâu và chú rể trong ngày "
        "trọng đại nhất cuộc đời!\n\n"
        "Tình yêu của hai bạn đã vượt qua bao thử thách để đơm hoa kết trái, và hôm nay, trước sự "
        "chứng kiến của gia đình, bạn bè, hai bạn chính thức về chung một nhà.\n\n"
        "Xin chúc cô dâu chú rể trăm năm hạnh phúc, bạc đầu răng long, sớm sinh quý tử!"
    ),
}


def _build_generic_script(topic_label: str, region_label: str) -> str:
    """Dựng kịch bản theo mẫu chung cho các vùng miền chưa có bản biên soạn riêng
    (Đà Nẵng, Hà Nội, TP. Hồ Chí Minh...), dựa trên tên thành phố / dòng sông đặc trưng."""
    info = REGIONS[region_label]
    city = info["noun_phrase"]
    river = info["landmark"]

    if topic_label.startswith("🏢"):
        return (
            f"Tọa lạc bên dòng {river} thơ mộng, ngay giữa lòng {city}, dự án khu đô thị mới "
            f"tự hào mang đến một chuẩn sống thượng lưu chưa từng có tại khu vực.\n\n"
            f"Không chỉ là nơi an cư, đây còn là biểu tượng phồn vinh mới - nơi hội tụ trọn vẹn hệ "
            f"sinh thái tiện ích đẳng cấp quốc tế: quảng trường ánh sáng, phố đi bộ thương mại, công "
            f"viên trung tâm, trường học liên cấp và bệnh viện quốc tế, tất cả trong tầm tay cư dân.\n\n"
            f"Với thiết kế kiến trúc sang trọng cùng chính sách bán hàng ưu đãi vượt trội dành riêng "
            f"cho một trăm khách hàng đầu tiên, đây chính là cơ hội đầu tư vàng không thể bỏ lỡ trong "
            f"năm nay.\n\n"
            f"Cơ hội sở hữu bất động sản ven {river} đang đến rất gần. Quý khách hàng vui lòng liên hệ "
            f"ngay hotline, hoặc Zalo không không chín bảy bảy, sáu tám bảy, hai hai bảy để được tư "
            f"vấn và giữ chỗ sớm nhất. Số không chín bảy bảy chấm sáu tám bảy chấm hai hai bảy."
        )
    if topic_label.startswith("📰"):
        return (
            f"Bản tin chuyển động đô thị hôm nay xin gửi tới quý vị và các bạn những thông tin nổi "
            f"bật về tốc độ phát triển hạ tầng tại {city}.\n\n"
            f"Trong những năm gần đây, khu vực này đang chuyển mình mạnh mẽ để trở thành một trong "
            f"những trung tâm kinh tế, văn hóa quan trọng của cả nước. Hàng loạt tuyến đường huyết "
            f"mạch được mở rộng, nhiều khu đô thị mới quy mô lớn lần lượt được khởi công, kéo theo "
            f"làn sóng dịch chuyển dân cư và dòng vốn đầu tư đổ về ngày càng mạnh mẽ.\n\n"
            f"Theo đánh giá của giới chuyên gia, quy hoạch mở rộng cùng với sự xuất hiện của các nhà "
            f"đầu tư chiến lược đã và đang tạo ra một diện mạo hoàn toàn mới cho khu vực, hứa hẹn trở "
            f"thành điểm sáng đáng sống trong thập kỷ tới.\n\n"
            f"Chương trình chuyển động đô thị đến đây xin tạm dừng. Xin kính chào và hẹn gặp lại quý "
            f"vị trong những bản tin tiếp theo."
        )
    if topic_label.startswith("📖"):
        return (
            f"Có một buổi chiều, tôi tình cờ ghé qua khu dân cư ven {river}, và cảm giác đầu tiên khi "
            f"bước chân xuống xe là một sự bình yên đến lạ.\n\n"
            f"Gió từ sông thổi vào mát rượi, xa xa là hàng cây xanh rợp bóng chạy dọc theo bờ kè, tiếng "
            f"trẻ con nô đùa trong công viên nội khu khiến tôi bất giác mỉm cười. Không gian sống nơi "
            f"đây thực sự khác biệt so với sự ồn ào, ngột ngạt của phố thị mà tôi vẫn quen thuộc mỗi "
            f"ngày.\n\n"
            f"Ngồi nhâm nhi ly cà phê ven sông, ngắm hoàng hôn buông xuống mặt nước lấp lánh, tôi chợt "
            f"nhận ra đây chính xác là hình ảnh chốn an cư mà bao người vẫn hằng mơ ước.\n\n"
            f"Nếu bạn cũng đang tìm kiếm một nơi để trở về sau ngày dài mệt mỏi, tôi nghĩ khu đô thị "
            f"ven {river} này tại {city} rất xứng đáng để bạn dành thời gian ghé thăm và trải nghiệm."
        )
    if topic_label.startswith("📢"):
        return (
            f"Bạn đang tìm kiếm một sản phẩm chất lượng, được hàng ngàn khách hàng tin dùng tại "
            f"{city}? Xin giới thiệu đến quý khách bộ sản phẩm mới nhất, được nghiên cứu và phát "
            f"triển dành riêng cho người tiêu dùng tại khu vực.\n\n"
            f"Với chất lượng vượt trội, thiết kế tinh tế cùng mức giá vô cùng hợp lý, sản phẩm của "
            f"chúng tôi cam kết mang đến sự hài lòng tuyệt đối ngay từ lần sử dụng đầu tiên.\n\n"
            f"Nhân dịp khai trương chi nhánh mới tại {city}, chúng tôi dành tặng ưu đãi giảm giá đặc "
            f"biệt lên đến ba mươi phần trăm cho một trăm khách hàng đặt mua sớm nhất.\n\n"
            f"Đừng bỏ lỡ cơ hội này! Quý khách vui lòng liên hệ ngay hotline, hoặc Zalo không không "
            f"chín bảy bảy, sáu tám bảy, hai hai bảy để được tư vấn miễn phí và nhận ưu đãi ngay "
            f"hôm nay."
        )
    if topic_label.startswith("🎓"):
        return (
            f"Chào mừng các bạn học viên đã đến với bài học hôm nay, được thực hiện bởi đội ngũ "
            f"giảng viên giàu kinh nghiệm tại trung tâm đào tạo {city}.\n\n"
            f"Trong bài học này, chúng ta sẽ cùng nhau tìm hiểu những kiến thức nền tảng quan trọng, "
            f"được trình bày một cách dễ hiểu, có ví dụ minh họa cụ thể, giúp các bạn nắm vững nội "
            f"dung chỉ sau một buổi học.\n\n"
            f"Hãy chuẩn bị giấy bút, tập trung theo dõi bài giảng, và đừng ngần ngại ghi lại những "
            f"câu hỏi để chúng ta cùng thảo luận ở phần cuối bài học.\n\n"
            f"Bây giờ, chúng ta hãy cùng bắt đầu bài học đầu tiên nhé!"
        )
    if topic_label.startswith("🎧"):
        return (
            f"Xin chào tất cả các bạn, chào mừng các bạn đã quay trở lại với podcast của chúng tôi, "
            f"nơi mỗi tuần chúng ta cùng nhau trò chuyện về những câu chuyện đời thường thật gần "
            f"gũi.\n\n"
            f"Số phát sóng hôm nay, mình muốn kể cho các bạn nghe về một buổi chiều lang thang dọc "
            f"{river}, {city} - nơi mình tình cờ gặp gỡ những con người bình dị nhưng mang trong "
            f"mình biết bao câu chuyện thú vị.\n\n"
            f"Nếu các bạn cũng có những kỷ niệm đáng nhớ về mảnh đất này, đừng ngần ngại để lại bình "
            f"luận, mình rất mong được lắng nghe câu chuyện của các bạn.\n\n"
            f"Cảm ơn các bạn đã lắng nghe, hẹn gặp lại trong số phát sóng tuần sau!"
        )
    # MC Sự Kiện / Đám Cưới
    return (
        f"Kính thưa quý vị quan khách, cô dâu chú rể cùng toàn thể gia đình hai họ! Trong không khí "
        f"ấm áp và hạnh phúc tại {city} hôm nay, chúng ta cùng nhau hội tụ để chứng kiến khoảnh khắc "
        f"thiêng liêng - lễ thành hôn của đôi uyên ương.\n\n"
        f"Xin một tràng pháo tay thật lớn để chào đón sự xuất hiện của cô dâu và chú rể trong ngày "
        f"trọng đại nhất cuộc đời!\n\n"
        f"Tình yêu của hai bạn đã vượt qua bao thử thách để đơm hoa kết trái, và hôm nay, trước sự "
        f"chứng kiến của gia đình, bạn bè, hai bạn chính thức về chung một nhà.\n\n"
        f"Xin chúc cô dâu chú rể trăm năm hạnh phúc, bạc đầu răng long, sớm sinh quý tử!"
    )


def get_script_text(topic_label: str, region_label: str) -> str:
    """Trả về nội dung kịch bản tương ứng với chủ đề + vùng miền đã chọn."""
    if topic_label == "✍️ Tự nhập văn bản tự do":
        return ""
    key = (topic_label, region_label)
    if key in CURATED_SCRIPTS:
        return CURATED_SCRIPTS[key]
    return _build_generic_script(topic_label, region_label)

# =====================================================================================
# 4. XỬ LÝ BẤT ĐỒNG BỘ - GỌI EDGE-TTS
# =====================================================================================
async def _synthesize_speech(text: str, voice_id: str, rate: str, pitch: str) -> bytes:
    """
    Kết nối tới edge-tts.Communicate và stream dữ liệu âm thanh dạng bytes.
    Trả về toàn bộ nội dung audio (định dạng MP3) dưới dạng bytes.
    """
    communicate = edge_tts.Communicate(text=text, voice=voice_id, rate=rate, pitch=pitch)
    audio_buffer = io.BytesIO()

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_buffer.write(chunk["data"])
        # chunk["type"] == "WordBoundary" -> bỏ qua, không cần cho việc xuất file audio

    return audio_buffer.getvalue()


def run_async_task(coro):
    """
    Wrapper an toàn để chạy một coroutine bất đồng bộ (asyncio) bên trong
    môi trường đồng bộ của Streamlit, tránh lỗi "no current event loop"
    có thể xảy ra tùy theo phiên bản Python / hệ điều hành.
    """
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


def generate_voice(text: str, voice_id: str, rate_value: int, pitch_value: int) -> bytes:
    """Chuẩn hóa tham số rate/pitch theo định dạng edge-tts yêu cầu rồi gọi TTS."""
    rate_str = f"{rate_value:+d}%"
    pitch_str = f"{pitch_value:+d}Hz"
    return run_async_task(_synthesize_speech(text, voice_id, rate_str, pitch_str))


# =====================================================================================
# 4b. CHẾ ĐỘ HỘI THOẠI NHIỀU GIỌNG (2-3 NGƯỜI NÓI CHUYỆN)
# =====================================================================================
def parse_dialogue_script(script: str, speaker_names: list) -> list:
    """
    Phân tách kịch bản hội thoại thành danh sách các lượt thoại [(tên_người_nói, nội_dung), ...].
    Mỗi lượt thoại mới bắt đầu bằng một dòng có dạng "Tên người nói: nội dung" - tên phải khớp
    (không phân biệt hoa/thường) với một trong các tên người nói đã cấu hình. Các dòng tiếp theo
    không có tiền tố tên hợp lệ sẽ được nối vào lượt thoại hiện tại (cho phép đoạn văn nhiều dòng).
    """
    name_lookup = {name.strip().lower(): name for name in speaker_names if name.strip()}
    turns = []
    current_speaker = None
    current_lines = []

    def flush():
        if current_speaker is not None:
            text = " ".join(line for line in current_lines if line).strip()
            if text:
                turns.append((current_speaker, text))

    for raw_line in script.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        matched = False
        if ":" in line:
            prefix, rest = line.split(":", 1)
            key = prefix.strip().lower()
            if key in name_lookup:
                flush()
                current_speaker = name_lookup[key]
                current_lines = [rest.strip()]
                matched = True
        if not matched:
            if current_speaker is None:
                continue  # Dòng đầu tiên không xác định được người nói -> bỏ qua
            current_lines.append(line)

    flush()
    return turns


def generate_dialogue_audio(
    turns: list,
    speaker_voice_map: dict,
    speaker_pitch_map: dict,
    rate_value: int,
    base_pitch_value: int,
    pause_ms: int = 450,
) -> bytes:
    """
    Tạo giọng đọc cho từng lượt thoại (mỗi lượt dùng giọng + cao độ riêng của người nói đó),
    sau đó ghép nối tất cả lại thành MỘT file MP3 duy nhất, có khoảng lặng ngắn giữa các lượt
    để nghe tự nhiên như một cuộc hội thoại thật. Yêu cầu ffmpeg (khai báo trong packages.txt).
    """
    combined = AudioSegment.silent(duration=0)

    for speaker, text in turns:
        voice_id = speaker_voice_map[speaker]
        total_pitch = base_pitch_value + speaker_pitch_map.get(speaker, 0)
        total_pitch = max(-50, min(50, total_pitch))  # giữ trong khoảng an toàn
        segment_bytes = generate_voice(text, voice_id, rate_value, total_pitch)
        segment = AudioSegment.from_file(io.BytesIO(segment_bytes), format="mp3")
        combined += segment + AudioSegment.silent(duration=pause_ms)

    buffer = io.BytesIO()
    combined.export(buffer, format="mp3", bitrate="128k")
    return buffer.getvalue()


# =====================================================================================
# 5. KHỞI TẠO SESSION STATE
# =====================================================================================
DEFAULT_TOPIC_KEY = "🏢 Bất Động Sản (Sang trọng / Thôi thúc)"
DEFAULT_REGION_KEY = "Nghệ An (TP Vinh)"

if "script_text" not in st.session_state:
    st.session_state.script_text = get_script_text(DEFAULT_TOPIC_KEY, DEFAULT_REGION_KEY)

if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None

if "last_voice_label" not in st.session_state:
    st.session_state.last_voice_label = None


def _apply_template():
    """Callback: khi người dùng đổi chủ đề hoặc vùng miền, nạp lại nội dung mẫu tương ứng."""
    topic_choice = st.session_state.template_choice
    region_choice = st.session_state.get("region_choice", DEFAULT_REGION_KEY)
    st.session_state.script_text = get_script_text(topic_choice, region_choice)
    # Xóa audio cũ vì nội dung kịch bản đã thay đổi
    st.session_state.audio_bytes = None


def _on_toggle_foreign_voices():
    """Callback: khi tắt hiển thị giọng nước ngoài, tự động đưa lựa chọn về giọng Việt
    nếu đang chọn một giọng nước ngoài (tránh lỗi giọng đang chọn không còn trong danh sách)."""
    if not st.session_state.get("show_foreign_voices", False):
        if st.session_state.get("voice_choice") not in VN_VOICE_KEYS:
            st.session_state.voice_choice = VN_VOICE_KEYS[0]


# =====================================================================================
# 6. GIAO DIỆN CHÍNH (UI LAYOUT)
# =====================================================================================
st.title("🎙️ Trình Tạo Giọng Đọc AI Đa Chủ Đề")
st.caption(
    "Chuyển văn bản thành giọng nói tự nhiên bằng công nghệ Edge-TTS của Microsoft - "
    "Miễn phí 100%, không giới hạn, không cần API key."
)

app_mode = st.radio(
    "🎬 Chế độ tạo giọng đọc",
    options=["🗣️ Một giọng (Đơn)", "👥 Hội thoại nhiều giọng (2-3 người)"],
    horizontal=True,
    key="app_mode",
)
st.divider()

# =====================================================================================
# CHẾ ĐỘ 1: MỘT GIỌNG (ĐƠN)
# =====================================================================================
if app_mode == "🗣️ Một giọng (Đơn)":
    col_settings, col_content = st.columns([1, 2], gap="large")

    # ---------------------------- CỘT TRÁI: CẤU HÌNH ----------------------------
    with col_settings:
        st.subheader("⚙️ Cấu Hình Giọng Đọc")

        show_foreign = st.checkbox(
            "🌐 Hiện thêm giọng tiếng Anh / Anh-Anh (tuỳ chọn)",
            value=False,
            key="show_foreign_voices",
            on_change=_on_toggle_foreign_voices,
        )
        voice_options = list(VOICES.keys()) if show_foreign else VN_VOICE_KEYS

        voice_label = st.selectbox(
            "🎤 Chọn giọng đọc",
            options=voice_options,
            key="voice_choice",
            help="Chọn giọng đọc phù hợp với chủ đề nội dung của bạn.",
        )
        voice_info = VOICES[voice_label]
        st.info(voice_info["desc"], icon="🗣️")
        if not show_foreign:
            st.caption(
                "💡 Edge-TTS (Microsoft) hiện chỉ phát hành chính thức **2 giọng tiếng Việt** - "
                "Nam Minh (nam) và Hoài My (nữ). Đây là giới hạn từ phía Microsoft (chưa có giọng "
                "Việt thứ 3), không phải giới hạn của ứng dụng. Tick ô trên nếu cần thêm giọng "
                "tiếng Anh / Anh-Anh."
            )

        st.markdown("##### 📋 Kịch Bản Mẫu Theo Chủ Đề")
        topic_choice = st.selectbox(
            "Chọn nhanh một kịch bản mẫu (hoặc tự nhập văn bản)",
            options=TOPIC_OPTIONS,
            key="template_choice",
            on_change=_apply_template,
            index=0,
        )

        if topic_choice != "✍️ Tự nhập văn bản tự do":
            st.selectbox(
                "🗺️ Chọn vùng miền cho kịch bản",
                options=list(REGIONS.keys()),
                key="region_choice",
                on_change=_apply_template,
                index=0,
                help=(
                    "Nội dung kịch bản (địa danh, dòng sông, thành phố...) sẽ được tùy biến theo "
                    "vùng miền bạn chọn. Nghệ An và Huế có kịch bản biên soạn riêng chi tiết; các "
                    "vùng miền khác dùng mẫu chung có thể chỉnh sửa lại."
                ),
            )

        st.markdown("---")
        st.markdown("##### 🎛️ Tùy Chỉnh Âm Thanh")

        rate_value = st.slider(
            "⚡ Tốc độ đọc (Rate)",
            min_value=-50,
            max_value=50,
            value=0,
            step=1,
            format="%d%%",
            help="Điều chỉnh tốc độ đọc nhanh hoặc chậm hơn so với mặc định.",
        )

        pitch_value = st.slider(
            "🎵 Cao độ / Độ trầm (Pitch)",
            min_value=-20,
            max_value=20,
            value=0,
            step=1,
            format="%d Hz",
            help="Điều chỉnh giọng đọc cao hoặc trầm hơn so với mặc định.",
        )

        st.caption(f"Thông số hiện tại: Rate = **{rate_value:+d}%** | Pitch = **{pitch_value:+d}Hz**")

    # ---------------------------- CỘT PHẢI: NỘI DUNG & KẾT QUẢ ----------------------------
    with col_content:
        st.subheader("📝 Nội Dung Kịch Bản")

        text_input = st.text_area(
            label="Văn bản cần chuyển thành giọng nói",
            key="script_text",
            height=320,
            placeholder="Nhập hoặc dán văn bản của bạn vào đây, hoặc chọn một kịch bản mẫu ở cột bên trái...",
        )

        char_count = len(text_input.strip())
        st.caption(f"Số ký tự: {char_count}")

        generate_clicked = st.button(
            "🚀 Tạo Giọng Đọc Ngay",
            type="primary",
            use_container_width=True,
            disabled=(char_count == 0),
        )

        if generate_clicked:
            if char_count == 0:
                st.warning("⚠️ Vui lòng nhập văn bản trước khi tạo giọng đọc.")
            else:
                try:
                    with st.spinner("🎧 Đang xử lý và tạo giọng đọc, vui lòng chờ trong giây lát..."):
                        audio_result = generate_voice(
                            text=text_input,
                            voice_id=voice_info["id"],
                            rate_value=rate_value,
                            pitch_value=pitch_value,
                        )

                    if audio_result:
                        st.session_state.audio_bytes = audio_result
                        st.session_state.last_voice_label = voice_label
                        st.success("✅ Tạo giọng đọc thành công!")
                    else:
                        st.error("❌ Không nhận được dữ liệu âm thanh. Vui lòng thử lại.")
                except Exception as e:
                    st.error(f"❌ Đã xảy ra lỗi trong quá trình tạo giọng đọc: {e}")

# =====================================================================================
# CHẾ ĐỘ 2: HỘI THOẠI NHIỀU GIỌNG (2-3 NGƯỜI NÓI CHUYỆN)
# =====================================================================================
else:
    st.subheader("👥 Tạo Hội Thoại Nhiều Giọng")
    st.caption(
        "Tạo một đoạn audio có 2-3 người nói chuyện với nhau, mỗi người một giọng riêng, tự "
        "động ghép nối liền mạch thành một file MP3 duy nhất - phù hợp làm podcast phỏng vấn, "
        "hội thoại quảng cáo, hoặc trích đoạn kịch."
    )

    num_speakers = st.radio(
        "Số người trong hội thoại", options=[2, 3], horizontal=True, key="num_speakers"
    )

    default_names = ["Người 1", "Người 2", "Người 3"]
    # Mặc định ưu tiên 2 giọng Việt; người thứ 3 (nếu có) tái dùng giọng Nam Minh với cao độ
    # khác để nghe tách biệt hơn - vì Edge-TTS chỉ có 2 giọng tiếng Việt.
    default_voice_keys = [VN_VOICE_KEYS[0], VN_VOICE_KEYS[1], VN_VOICE_KEYS[0]]
    default_pitch_offsets = [0, 0, 8]

    speaker_configs = []
    speaker_cols = st.columns(num_speakers)
    for i in range(num_speakers):
        with speaker_cols[i]:
            st.markdown(f"**Người nói #{i + 1}**")
            name = st.text_input("Tên", value=default_names[i], key=f"speaker_name_{i}")
            voice_sel = st.selectbox(
                "Giọng đọc",
                options=list(VOICES.keys()),
                index=list(VOICES.keys()).index(default_voice_keys[i]),
                key=f"speaker_voice_{i}",
            )
            pitch_offset = st.slider(
                "Cao độ riêng (Hz)",
                -20,
                20,
                default_pitch_offsets[i],
                key=f"speaker_pitch_{i}",
                help="Chỉnh lệch cao độ để phân biệt 2 người nói dùng chung 1 giọng gốc.",
            )
            speaker_configs.append(
                {
                    "name": name.strip() or default_names[i],
                    "voice_id": VOICES[voice_sel]["id"],
                    "pitch_offset": pitch_offset,
                }
            )

    if num_speakers == 3:
        st.caption(
            "💡 Vì Edge-TTS chỉ có 2 giọng tiếng Việt, người thứ 3 mặc định dùng lại giọng Nam "
            "Minh với cao độ lệch để nghe khác biệt hơn. Bạn có thể đổi giọng người thứ 3 sang "
            "tiếng Anh (mở dropdown Giọng đọc) nếu muốn 3 chất giọng hoàn toàn khác nhau."
        )

    st.markdown("##### 📝 Kịch Bản Hội Thoại")
    st.caption(
        "Mỗi dòng bắt đầu bằng **đúng tên người nói** (như đặt ở trên) + dấu hai chấm, ví dụ: "
        f"“{speaker_configs[0]['name']}: Xin chào...”. Dòng không có tên hợp lệ sẽ được "
        "nối vào lượt nói ngay trước đó."
    )

    _default_dialogue = (
        f"{speaker_configs[0]['name']}: Chào bạn, hôm nay chúng ta sẽ nói về chủ đề bất động sản "
        "tại thành phố Vinh nhé.\n"
        f"{speaker_configs[1]['name']}: Vâng, đây là chủ đề mình rất quan tâm. Dạo này thị trường "
        "ở Vinh phát triển mạnh lắm phải không?\n"
        f"{speaker_configs[0]['name']}: Đúng vậy, đặc biệt là các dự án khu đô thị ven sông Lam, "
        "được đầu tư bài bản và quy hoạch rất đẹp.\n"
        f"{speaker_configs[1]['name']}: Nghe hấp dẫn quá, để mình tìm hiểu thêm thông tin chi "
        "tiết."
    )
    if "dialogue_script" not in st.session_state:
        st.session_state.dialogue_script = _default_dialogue

    dialogue_script = st.text_area(
        "Nội dung hội thoại",
        key="dialogue_script",
        height=280,
        placeholder="Người 1: ...\nNgười 2: ...",
    )

    col_rate, col_pitch = st.columns(2)
    with col_rate:
        dialogue_rate = st.slider(
            "⚡ Tốc độ đọc chung (Rate)", -50, 50, 0, step=1, format="%d%%", key="dialogue_rate"
        )
    with col_pitch:
        dialogue_pitch = st.slider(
            "🎵 Cao độ nền chung (Pitch)", -20, 20, 0, step=1, format="%d Hz", key="dialogue_pitch"
        )

    dialogue_char_count = len(dialogue_script.strip())
    generate_dialogue_clicked = st.button(
        "🚀 Tạo Hội Thoại Ngay",
        type="primary",
        use_container_width=True,
        disabled=(dialogue_char_count == 0),
    )

    if generate_dialogue_clicked:
        speaker_names = [s["name"] for s in speaker_configs]
        turns = parse_dialogue_script(dialogue_script, speaker_names)
        if not turns:
            st.warning(
                "⚠️ Không nhận diện được lượt thoại nào. Mỗi dòng phải bắt đầu bằng đúng tên "
                "người nói đã đặt ở trên (không phân biệt hoa/thường), theo sau là dấu hai chấm."
            )
        else:
            try:
                with st.spinner(f"🎧 Đang tạo {len(turns)} lượt thoại và ghép thành 1 file..."):
                    speaker_voice_map = {s["name"]: s["voice_id"] for s in speaker_configs}
                    speaker_pitch_map = {s["name"]: s["pitch_offset"] for s in speaker_configs}
                    audio_result = generate_dialogue_audio(
                        turns,
                        speaker_voice_map,
                        speaker_pitch_map,
                        dialogue_rate,
                        dialogue_pitch,
                    )

                if audio_result:
                    st.session_state.audio_bytes = audio_result
                    st.session_state.last_voice_label = f"HoiThoai_{num_speakers}Nguoi"
                    st.success(f"✅ Đã tạo xong hội thoại gồm {len(turns)} lượt nói!")
                else:
                    st.error("❌ Không nhận được dữ liệu âm thanh. Vui lòng thử lại.")
            except Exception as e:
                st.error(f"❌ Đã xảy ra lỗi khi tạo hội thoại: {e}")

# =====================================================================================
# KHU VỰC PHÁT & TẢI FILE (DÙNG CHUNG CHO CẢ 2 CHẾ ĐỘ)
# =====================================================================================
if st.session_state.audio_bytes:
    st.divider()
    st.subheader("🔊 Nghe Thử & Tải Xuống")

    st.audio(st.session_state.audio_bytes, format="audio/mp3")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_voice_name = (
        (st.session_state.last_voice_label or "GiongDoc")
        .split(" - ")[0]
        .replace("🇻🇳", "")
        .replace("🇺🇸", "")
        .replace("🇬🇧", "")
        .strip()
        .replace(" ", "_")
    )
    file_name = f"GiongDoc_{safe_voice_name}_{timestamp}.mp3"

    st.download_button(
        label="⬇️ Tải File MP3 Về Máy",
        data=st.session_state.audio_bytes,
        file_name=file_name,
        mime="audio/mpeg",
        use_container_width=True,
    )

# =====================================================================================
# 7. FOOTER
# =====================================================================================
st.divider()
st.caption(
    "🎙️ Trình Tạo Giọng Đọc AI Đa Chủ Đề — Xây dựng bằng Streamlit & edge-tts (Microsoft). "
    "Công cụ miễn phí, không thu thập dữ liệu, không cần API key."
)
