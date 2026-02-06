import streamlit as st
from rectpack import newPacker
import rectpack.packer as packer
import random

# --- 1. ระบบรหัสผ่าน ---
PASSWORD = "CL3006"


def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("🔒 GlaCal Master (Smart Packing)")
        pwd = st.text_input("รหัสผ่าน", type="password")
        if st.button("เข้าสู่ระบบ"):
            if pwd == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("รหัสผ่านผิด!")
        return False
    return True


# --- 2. ฟังก์ชันคำนวณ (เน้นยัดแน่น ไม่ 1 ต่อ 1) ---
def run_fixed_simulation(stocks, pieces, allowance, trials=50):
    best_overall_results = None
    max_efficiency = -1

    # เรียงสต็อกใหญ่ไปเล็กเพื่อให้ระบบพิจารณาแผ่นใหญ่ก่อนเสมอ
    priority_stocks = sorted(stocks, key=lambda x: x['w'] * x['h'], reverse=True)

    progress_bar = st.progress(0, text="กำลังค้นหารูปแบบการวางที่คุ้มที่สุด...")

    for trial in range(trials):
        current_pieces = pieces.copy()
        random.shuffle(current_pieces)  # สุ่มลำดับชิ้นงานเพื่อหาจุดที่ลงตัวที่สุด

        # ใช้ BBF (Best-Bin-Fit) เพื่อให้ระบบเลือกยัดชิ้นงานลงในแผ่นให้แน่นที่สุด
        p_engine = newPacker(
            mode=packer.PackingMode.Offline,
            bin_algo=packer.PackingBin.BBF,
            pack_algo=packer.MaxRectsBssf,
            rotation=True
        )

        # ใส่แผ่นคลัง (ใส่จำนวนไว้เยอะๆ เพื่อให้ระบบเลือกใช้แผ่นที่ใหญ่และคุ้มที่สุดก่อน)
        for s in priority_stocks:
            p_engine.add_bin(s['w'], s['h'], count=100)

        # ใส่ชิ้นงานทั้งหมด
        for i, p in enumerate(current_pieces):
            p_engine.add_rect(p['w'] + allowance, p['h'] + allowance, rid=i)

        p_engine.pack()

        current_results = []
        total_bin_area = 0
        total_used_area = 0

        for b in p_engine:
            if len(b) > 0:
                bin_area = b.width * b.height
                # พื้นที่เนื้อกระจกจริงๆ
                actual_used = sum((r.width - allowance) * (r.height - allowance) for r in b)

                total_bin_area += bin_area
                total_used_area += actual_used

                current_results.append({
                    'sw': b.width,
                    'sh': b.height,
                    'area': bin_area,
                    'actual_used': actual_used,
                    'items': [{'w': r.width - allowance, 'h': r.height - allowance} for r in b]
                })

        if current_results:
            efficiency = total_used_area / total_bin_area
            # เลือกแผนการตัดที่ให้ความคุ้มค่า (Efficiency) สูงที่สุด
            if efficiency > max_efficiency:
                max_efficiency = efficiency
                best_overall_results = current_results

        progress_bar.progress((trial + 1) / trials)

    progress_bar.empty()
    return best_overall_results


# --- 3. UI ---
st.set_page_config(page_title="GlaCal Master Pro", layout="wide")

if check_password():
    if 'stocks' not in st.session_state:
        st.session_state.stocks = [{'w': 48.0, 'h': 96.0}]
    if 'projects' not in st.session_state:
        st.session_state.projects = [{'name': 'ชุดงานที่ 1', 'items': [{'w': 20.0, 'h': 20.0, 'qty': 1}]}]

    with st.sidebar:
        st.title("⚙️ คลังสินค้า")
        allowance = st.number_input("ระยะเผื่อหักกระจก (นิ้ว)", value=0.125, format="%.4f")
        st.divider()
        for si, s in enumerate(st.session_state.stocks):
            with st.container(border=True):
                c1, c2, c3 = st.columns([0.4, 0.4, 0.2])
                s['w'] = c1.number_input(f"กว้าง", value=float(s['w']), key=f"sw_{si}")
                s['h'] = c2.number_input(f"สูง", value=float(s['h']), key=f"sh_{si}")
                if c3.button("❌", key=f"del_s_{si}"):
                    st.session_state.stocks.pop(si);
                    st.rerun()
        st.button("➕ เพิ่มขนาดคลัง", on_click=lambda: st.session_state.stocks.append({'w': 36.0, 'h': 72.0}))

    st.title("🖼️ GlaCal Master: ระบบคำนวณตัดกระจก (เน้นยัดงานแน่น)")

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

            if st.button("➕ เพิ่มชิ้นงาน", key=f"add_it_{p_idx}"):
                proj['items'].append({'w': 10.0, 'h': 10.0, 'qty': 1});
                st.rerun()

            st.divider()
            if st.button(f"🚀 คำนวณ (Best Fit Optimization)", key=f"calc_{p_idx}", type="primary"):
                stocks_data = st.session_state.stocks
                pieces_data = [{'w': it['w'], 'h': it['h']} for it in proj['items'] for _ in range(int(it['qty']))]

                results = run_fixed_simulation(stocks_data, pieces_data, allowance)

                if results:
                    st.success(f"📊 สรุป: ใช้กระจกทั้งหมด {len(results)} แผ่น")
                    res_grid = st.columns(3)
                    for idx, s in enumerate(results):
                        with res_grid[idx % 3]:
                            with st.expander(f"แผ่นที่ {idx + 1}: {s['sw']}x{s['sh']}", expanded=True):
                                eff = (s['actual_used'] / s['area']) * 100
                                st.write(f"📊 ประสิทธิภาพ: **{eff:.1f}%**")
                                st.write(f"♻️ เศษเหลือ: **{(s['area'] - s['actual_used']):.2f}** ตร.นิ้ว")
                                st.progress(min(eff / 100, 1.0))
                                for p in s['items']:
                                    st.code(f"✂️ {p['w']} x {p['h']} นิ้ว")
                else:
                    st.error("❌ ชิ้นงานใหญ่เกินไป หรือคลังสินค้าไม่เพียงพอ")
