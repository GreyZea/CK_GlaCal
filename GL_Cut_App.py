import streamlit as st
from rectpack import newPacker

# --- 1. ระบบรหัสผ่าน ---
PASSWORD = "CK3006"


def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("🔒 GlaCal Master (Industrial Engine)")
        pwd = st.text_input("รหัสผ่าน", type="password")
        if st.button("เข้าสู่ระบบ"):
            if pwd == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("รหัสผ่านผิด!")
        return False
    return True


# --- 2. ฟังก์ชันคำนวณโดยใช้ rectpack (มาตรฐานอุตสาหกรรม) ---
def calculate_packing_industrial(stocks, pieces, allowance):
    # สร้างระบบ Packer
    packer = newPacker(rotation=True)  # อนุญาตให้หมุนชิ้นงานได้

    # 1. เพิ่มแผ่นกระจกในคลัง (เรียงแผ่นใหญ่ไปเล็กเพื่อให้ Packer เลือกใช้ตามความเหมาะสม)
    for i, s in enumerate(stocks):
        # ใส่จำนวนแผ่นเป็น infinity (หรือใส่จำนวนจำกัดตามจริงได้)
        packer.add_bin(s['w'], s['h'], count=float('inf'))

    # 2. เพิ่มชิ้นงานที่ต้องการตัด (บวกระยะเผื่อหักกระจกเข้าไปในชิ้นงานเลย)
    for i, p in enumerate(pieces):
        packer.add_rect(p['w'] + allowance, p['h'] + allowance)

    # 3. เริ่มการคำนวณ (ใช้ Algorithm แบบ Best Fit)
    packer.pack()

    # 4. รวบรวมผลลัพธ์
    all_results = []
    for b in packer:
        if len(b) > 0:
            used_area = sum(rect.width * rect.height for rect in b)
            all_results.append({
                'width': b.width,
                'height': b.height,
                'used_area': used_area,
                'rects': [{'w': r.width - allowance, 'h': r.height - allowance} for r in b]
            })

    return all_results


# --- 3. ส่วนหน้าจอ App ---
st.set_page_config(page_title="GlaCal Industrial", layout="wide")

if check_password():
    if 'stocks' not in st.session_state:
        st.session_state.stocks = [{'w': 48.0, 'h': 96.0}]
    if 'projects' not in st.session_state:
        st.session_state.projects = [{'name': 'ชุดที่ 1', 'items': [{'w': 20.0, 'h': 20.0, 'qty': 1}]}]

    with st.sidebar:
        st.title("⚙️ คลังกระจก")
        allowance = st.number_input("ระยะเผื่อหัก (นิ้ว)", value=0.125, format="%.4f")
        for si, s in enumerate(st.session_state.stocks):
            with st.container(border=True):
                c1, c2, c3 = st.columns([0.4, 0.4, 0.2])
                s['w'] = c1.number_input(f"กว้าง", value=float(s['w']), key=f"sw_{si}")
                s['h'] = c2.number_input(f"สูง", value=float(s['h']), key=f"sh_{si}")
                if c3.button("❌", key=f"del_s_{si}"):
                    st.session_state.stocks.pop(si);
                    st.rerun()
        st.button("➕ เพิ่มแผ่นคลัง", on_click=lambda: st.session_state.stocks.append({'w': 36.0, 'h': 72.0}))

    st.title("🖼️ GlaCal: ระบบคำนวณตัดกระจก (อ้างอิง Algorithm สากล)")

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

            c_btn1, _ = st.columns([0.15, 0.85])
            with c_btn1:
                if st.button("➕ เพิ่มชิ้นงาน", key=f"add_it_{p_idx}"):
                    proj['items'].append({'w': 10.0, 'h': 10.0, 'qty': 1});
                    st.rerun()

            if st.button(f"🚀 คำนวณผลลัพธ์", key=f"calc_{p_idx}", type="primary"):
                # เตรียมข้อมูล
                stocks_data = st.session_state.stocks
                pieces_data = [{'w': it['w'], 'h': it['h']} for it in proj['items'] for _ in range(int(it['qty']))]

                results = calculate_packing_industrial(stocks_data, pieces_data, allowance)

                if results:
                    st.success(f"📊 สรุป: ใช้ทั้งหมด {len(results)} แผ่น")
                    res_grid = st.columns(3)
                    for idx, s in enumerate(results):
                        with res_grid[idx % 3]:
                            with st.expander(f"แผ่นที่ {idx + 1}: {s['width']}x{s['height']}", expanded=True):
                                efficiency = (s['used_area'] / (s['width'] * s['height'])) * 100
                                st.write(f"📊 ประสิทธิภาพ: **{efficiency:.1f}%**")
                                st.write(f"♻️ เศษเหลือ: **{(s['width'] * s['height'] - s['used_area']):.2f}** ตร.นิ้ว")
                                st.progress(min(efficiency / 100, 1.0))
                                for p in s['rects']:
                                    st.code(f"✂️ {p['w']} x {p['h']} นิ้ว")
                else:
                    st.error("❌ ไม่สามารถคำนวณได้ โปรดตรวจสอบขนาดชิ้นงานเทียบกับคลัง")
