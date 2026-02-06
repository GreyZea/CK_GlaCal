import streamlit as st
from rectpack import newPacker
import rectpack.packer as packer
import random

# --- 1. ระบบรหัสผ่าน ---
PASSWORD = "CK3006"


def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("🔒 GlaCal Master (Smart Big-Sheet)")
        pwd = st.text_input("รหัสผ่าน", type="password")
        if st.button("เข้าสู่ระบบ"):
            if pwd == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("รหัสผ่านผิด!")
        return False
    return True


# --- 2. ฟังก์ชันคำนวณ (ยัดให้แน่น + เลือกแผ่นใหญ่เป็นลำดับแรก) ---
def run_smart_simulation(stocks, pieces, allowance, trials=50):
    best_overall_results = None
    max_score = -1  # ใช้คะแนนความคุ้มค่าเป็นตัวตัดสิน

    progress_text = "กำลังคำนวณหารูปแบบที่คุ้มค่าที่สุด (เน้นแผ่นใหญ่)..."
    my_bar = st.progress(0, text=progress_text)

    # เรียงคลังจากใหญ่ไปเล็ก เพื่อให้ระบบเห็นแผ่นใหญ่เป็นลำดับแรกในการพิจารณา
    sorted_stocks = sorted(stocks, key=lambda x: x['w'] * x['h'], reverse=True)

    for trial in range(trials):
        current_pieces = pieces.copy()
        random.shuffle(current_pieces)  # สลับลำดับชิ้นงานเพื่อหาจุดที่ "ลงตัว" ที่สุด

        # ใช้โหมด Offline + Global Bin Fit เพื่อให้คำนวณภาพรวมทั้งโปรเจกต์
        packer_engine = newPacker(
            mode=packer.PackingMode.Offline,
            bin_algo=packer.PackingBin.BBF,  # Best-Bin-Fit (ฉลาดที่สุดในการเลือกแผ่น)
            pack_algo=packer.MaxRectsBssf,
            rotation=True
        )

        for s in sorted_stocks:
            packer_engine.add_bin(s['w'], s['h'], count=100)

        for i, p in enumerate(current_pieces):
            packer_engine.add_rect(p['w'] + allowance, p['h'] + allowance, rid=i)

        packer_engine.pack()

        current_results = []
        total_used_area = 0
        total_bin_area = 0

        for b in packer_engine:
            if len(b) > 0:
                bin_area = b.width * b.height
                used_area_in_bin = sum((r.width - allowance) * (r.height - allowance) for r in b)

                total_used_area += used_area_in_bin
                total_bin_area += bin_area

                current_results.append({
                    'width': b.width,
                    'height': b.height,
                    'area': bin_area,
                    'used_area': used_area_in_bin,
                    'rects': [{'w': r.width - allowance, 'h': r.height - allowance} for r in b]
                })

        if current_results:
            # สูตรคำนวณคะแนน: เน้นประสิทธิภาพพื้นที่ (Efficiency) เป็นหลัก
            efficiency = total_used_area / total_bin_area

            # ถ้าความคุ้มค่าดีกว่าเดิม ให้เก็บผลลัพธ์นี้ไว้
            if efficiency > max_score:
                max_score = efficiency
                best_overall_results = current_results

        my_bar.progress((trial + 1) / trials, text=progress_text)

    my_bar.empty()
    return best_overall_results


# --- 3. UI ---
st.set_page_config(page_title="GlaCal Smart Optimizer", layout="wide")

if check_password():
    if 'stocks' not in st.session_state:
        st.session_state.stocks = [{'w': 48.0, 'h': 96.0}]
    if 'projects' not in st.session_state:
        st.session_state.projects = [{'name': 'งานตัดชุดที่ 1', 'items': [{'w': 20.0, 'h': 20.0, 'qty': 1}]}]

    with st.sidebar:
        st.title("⚙️ คลังสินค้า")
        allowance = st.number_input("ระยะเผื่อหัก (นิ้ว)", value=0.125, format="%.4f")
        for si, s in enumerate(st.session_state.stocks):
            with st.container(border=True):
                c1, c2, c3 = st.columns([0.4, 0.4, 0.2])
                s['w'] = c1.number_input(f"กว้าง", value=float(s['w']), key=f"sw_{si}")
                s['h'] = c2.number_input(f"สูง", value=float(s['h']), key=f"sh_{si}")
                if c3.button("❌", key=f"del_s_{si}"):
                    st.session_state.stocks.pop(si);
                    st.rerun()
        st.button("➕ เพิ่มขนาดคลัง", on_click=lambda: st.session_state.stocks.append({'w': 36.0, 'h': 72.0}))

    st.title("🖼️ GlaCal Master: ระบบคำนวณความคุ้มค่าสูงสุด")
    st.info("💡 ระบบจะคำนวณให้ยัดชิ้นงานได้แน่นที่สุด โดยเลือกใช้แผ่นกระจกที่เหมาะสมที่สุดจากคลังเพื่อลดเศษเหลือ")

    for p_idx, proj in enumerate(st.session_state.projects):
        with st.container(border=True):
            proj['name'] = st.text_input("ชื่อโปรเจกต์", value=proj['name'], key=f"pname_{p_idx}")

            for i, it in enumerate(proj['items']):
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([0.35, 0.35, 0.2, 0.1])
                    it['w'] = c1.number_input(f"กว้าง", value=float(it['w']), key=f"w_{p_idx}_{i}")
                    it['h'] = c2.number_input(f"สูง", value=float(it['h']), key=f"h_{p_idx}_{i}")
                    it['qty'] = c3.number_input(f"จำนวน", value=int(it['qty']), min_value=1, key=f"q_{p_idx}_{i}")
                    if c4.button("❌", key=f"del_it_{p_idx}_{i}"):
                        proj['items'].pop(i);
                        st.rerun()

            if st.button(f"🚀 เริ่มคำนวณผลลัพธ์", key=f"calc_{p_idx}", type="primary"):
                stocks_data = st.session_state.stocks
                pieces_data = [{'w': it['w'], 'h': it['h']} for it in proj['items'] for _ in range(int(it['qty']))]

                results = run_smart_simulation(stocks_data, pieces_data, allowance, trials=50)

                if results:
                    total_area_all = sum(s['area'] for s in results)
                    total_used_all = sum(s['used_area'] for s in results)
                    overall_eff = (total_used_all / total_area_all) * 100

                    st.success(f"📊 สรุป: ใช้ {len(results)} แผ่น | ความคุ้มค่ารวม {overall_eff:.1f}%")

                    res_grid = st.columns(3)
                    for idx, s in enumerate(results):
                        with res_grid[idx % 3]:
                            with st.expander(f"แผ่นที่ {idx + 1}: {s['width']}x{s['height']}", expanded=True):
                                eff = (s['used_area'] / s['area']) * 100
                                st.write(f"📊 ประสิทธิภาพ: **{eff:.1f}%**")
                                st.write(f"♻️ เศษเหลือ: **{(s['area'] - s['used_area']):.2f}** ตร.นิ้ว")
                                st.progress(min(eff / 100, 1.0))
                                for p in s['rects']:
                                    st.code(f"✂️ {p['w']} x {p['h']} นิ้ว")
                else:
                    st.error("❌ ไม่สามารถคำนวณได้")
