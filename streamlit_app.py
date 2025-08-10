import streamlit as st
from datetime import datetime
import re

import base64
import os
import streamlit as st

# ✅ 페이지: centered 유지 + 본문 폭만 CSS로 확장(중간 사이즈)
st.set_page_config(page_title="DB생명 당월 수수료 계산기", layout="centered")
st.markdown(
    """
    <style>
    .block-container {
        max-width: 1300px;     /* 필요시 1300~1500px로 조절 */
        padding-left: 2rem;
        padding-right: 2rem;
    }
    label.css-16idsys, label.css-1p3cay5 {
        white-space: nowrap;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def render_title_with_logo_right(logo_path: str, title_text: str, logo_width: int = 100):
    try:
        if not os.path.exists(logo_path):
            raise FileNotFoundError(logo_path)
        with open(logo_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px; border-bottom:1px solid #ddd; padding-bottom:4px;">
                <h1 style="margin:0; font-size:2.5rem;">📊 {title_text}</h1>
                <img src="data:image/png;base64,{b64}" width="{logo_width}" alt="DB생명 로고" />
            </div>
            """,
            unsafe_allow_html=True
        )
    except Exception:
        st.title(f"📊 {title_text}")

render_title_with_logo_right(
    logo_path="DB_logo.png",
    title_text="당월 수수료 계산기",
    logo_width=120
)

# 간격 유틸
def SP(px: int = 16):
    st.markdown(f"<div style='height:{px}px'></div>", unsafe_allow_html=True)

SP(25)

# ─────────────────────────────────────
# 상품 정의 (성적률: %)
# ─────────────────────────────────────
PRODUCTS = {
    "백년친구내가고른건강보험(2504)": 500,
    "백년친구700종신보험(2506)": 400,
    "백년친구알차고행복한플러스종신보험(2404)": 300,
}

# 상품별 허용 납입년도 옵션
PAY_YEARS = {
    "백년친구내가고른건강보험(2504)": ["10년", "20년", "30년"],
    "백년친구700종신보험(2506)": ["20년", "30년"],
    "백년친구알차고행복한플러스종신보험(2404)": ["5년", "7년", "10년"],
}

# 전략건강상품
STRATEGIC_HEALTH = {
    "백년친구내가고른건강보험(2504)",
    "백년친구700종신보험(2506)",
}

# ─────────────────────────────────────
# 세션 상태
# ─────────────────────────────────────
if "entries" not in st.session_state:
    st.session_state.entries = []
if "entry_seq" not in st.session_state:
    st.session_state.entry_seq = 0
if "product_selector" not in st.session_state:
    st.session_state.product_selector = "— 상품을 선택하세요 —"

# ─────────────────────────────────────
# 유틸: 통화 입력(실시간 3자리 콤마)
# ─────────────────────────────────────
def _format_currency(text_key: str):
    raw = st.session_state.get(text_key, "")
    digits = re.sub(r"[^0-9]", "", raw or "")
    num = int(digits) if digits else 0
    st.session_state[text_key] = f"{num:,}" if num else ""

def currency_input(label: str, key: str, default: int = 0, label_visibility: str = "visible") -> int:
    text_key = f"{key}_text"
    if text_key not in st.session_state:
        st.session_state[text_key] = f"{default:,}" if isinstance(default, int) and default else ""
    st.text_input(
        label,
        key=text_key,
        on_change=_format_currency,
        args=(text_key,),
        label_visibility=label_visibility,
    )
    digits = re.sub(r"[^0-9]", "", st.session_state.get(text_key, ""))
    return int(digits) if digits else 0

# ─────────────────────────────────────
# 기본 정보 입력
# ─────────────────────────────────────
st.subheader("📝 기본 정보 입력")
SP(25)

st.markdown("<div style='font-size:1.08rem; font-weight:700;'>✔️위임년월 입력</div>", unsafe_allow_html=True)
SP(12)

years = list(range(2025, 1988, -1))  # 2025 ~ 1989

c_year, c_gap, c_month, c_fill = st.columns([0.22, 0.02, 0.18, 0.58])

with c_year:
    y_col, _ = st.columns([0.45, 0.55])
    with y_col:
        year = st.selectbox("위임년도", options=years, index=0, key="year_select")

with c_gap:
    st.write("")

with c_month:
    m_col, _ = st.columns([0.45, 0.55])
    with m_col:
        month = st.selectbox("위임월", options=list(range(1, 13)), index=7, key="month_select")

with c_fill:
    st.write("")

st.markdown("""
<style>
div[data-testid="stSelectbox"]:has(#year_select) { width: 120px !important; }
div[data-testid="stSelectbox"]:has(#month_select) { width: 90px !important; }
</style>
""", unsafe_allow_html=True)

SP(20)
st.markdown("<div style='font-size:1.08rem; font-weight:700;'>✔️표준활동 입력</div>", unsafe_allow_html=True)
SP(8)
std_activity = st.checkbox("당월 표준활동 달성 여부", value=False)

SP(20)
st.markdown("<div style='font-size:1.08rem; font-weight:700;'>✔️유지율 입력</div>", unsafe_allow_html=True)
SP(8)

today = datetime.today()
contract_months_now = (today.year - year) * 12 + (today.month - month) + 1  # 1=1차월 ...

def _std_retention(month_idx: int):
    if month_idx <= 2:
        return None
    elif month_idx <= 6:
        return 93
    elif month_idx <= 12:
        return 90
    else:
        return 85

_std_now_dynamic = _std_retention(contract_months_now)
_std_13 = _std_retention(13)
_std_25 = _std_retention(25)

if "_ret_anchor" not in st.session_state:
    st.session_state._ret_anchor = (year, month)
if st.session_state._ret_anchor != (year, month):
    st.session_state["retention_1st_val"] = 0 if _std_now_dynamic is None else _std_now_dynamic
    st.session_state["retention_13th_val"] = _std_13 if _std_13 is not None else 85
    st.session_state["retention_25th_val"] = _std_25 if _std_25 is not None else 85
    st.session_state._ret_anchor = (year, month)

if "retention_1st_val" not in st.session_state:
    st.session_state["retention_1st_val"] = 0 if _std_now_dynamic is None else _std_now_dynamic
if "retention_13th_val" not in st.session_state:
    st.session_state["retention_13th_val"] = _std_13 if _std_13 is not None else 85
if "retention_25th_val" not in st.session_state:
    st.session_state["retention_25th_val"] = _std_25 if _std_25 is not None else 85

ret1, ret13, ret25 = st.columns(3)
with ret1:
    retention_1st = st.slider("당월 유지율 (%)", min_value=0, max_value=100, key="retention_1st_val")
    st.markdown(
        f"<div style='font-size:0.8rem; font-weight:400; color:#f70a12;'>기준 유지율: {'해당사항없음' if _std_now_dynamic is None else str(_std_now_dynamic)+'%'}</div>",
        unsafe_allow_html=True
    )

with ret13:
    retention_13th = st.slider("13회차 납입 시점 예상 유지율 (%)", min_value=50, max_value=100, key="retention_13th_val")
    st.markdown(
        f"<div style='font-size:0.8rem; font-weight:400; color:#f70a12;'>기준 유지율: {'해당사항없음' if _std_13 is None else str(_std_13)+'%'}</div>",
        unsafe_allow_html=True
    )

with ret25:
    retention_25th = st.slider("25회차 납입 시점 예상 유지율 (%)", min_value=50, max_value=100, key="retention_25th_val")
    st.markdown(
        f"<div style='font-size:0.8rem; font-weight:400; color:#f70a12;'>기준 유지율: {'해당사항없음' if _std_25 is None else str(_std_25)+'%'}</div>",
        unsafe_allow_html=True
    )

# ▶ 유효환산/정착보장 관련 추가 입력
SP(40)
st.markdown("<div style='font-size:1.08rem; font-weight:700;'>✔️유효환산/정착보장 산출 제반사항 입력</div>", unsafe_allow_html=True)
SP(10)
cA, cB, cC = st.columns([1, 1, 1])
with cA:
    refund_p = currency_input("당월 예상 환수성적 (* 청철/반송/무효/해지)", key="refund_p", default=0)
with cB:
    refund_amt = currency_input("당월 예상 환수금 (* 모집+성과1+초기2 환수금)", key="refund_amt", default=0)
with cC:
    direct_recruits = st.number_input("당월 직도입 인원(명)", min_value=0, max_value=99, value=0, step=1)

st.markdown("---")

# ─────────────────────────────────────
# 상품 선택 → 자동 추가
# ─────────────────────────────────────
options = ["— 상품을 선택하세요 —"] + list(PRODUCTS.keys())

def on_select_change():
    choice = st.session_state.product_selector
    if choice and choice != options[0]:
        st.session_state.entry_seq += 1
        new_id = st.session_state.entry_seq
        default_pay_year = PAY_YEARS.get(choice, ["기타"])[0]
        st.session_state.entries.append({
            "id": new_id,
            "product": choice,
            "pay_year": default_pay_year,
            "pay_year_key": f"payyear_{new_id}",
            "premium_key": f"premium_{new_id}",
            "premium": 0,
        })
        st.session_state.product_selector = options[0]

st.markdown("<div style='font-size:1.08rem; font-weight:700; color:#000000;'>✔️상품 선택</div>", unsafe_allow_html=True)
st.caption("※ 선택 즉시 아래에 계약이 추가됩니다")
st.selectbox("", options=options, key="product_selector", on_change=on_select_change)

# ─────────────────────────────────────
# 등록된 계약 렌더링
# ─────────────────────────────────────
SP(10)
st.subheader("🧾 상품 목록")
if not st.session_state.entries:
    st.info("상품을 선택하면 아래에 계약이 추가됩니다. 동일 상품을 여러 건 추가할 수 있습니다.")
else:
    h1, h2, h3, h4 = st.columns([5.2, 1.6, 1.8, 1.1])
    with h1: st.markdown("**상품명**")
    with h2: st.markdown("**납입년도**")
    with h3: st.markdown("**월초 보험료(원)**")
    with h4: st.markdown("**삭제**")

    remove_id = None
    for e in st.session_state.entries:
        c1, c2, c3, c4 = st.columns([5.2, 1.6, 1.8, 1.1])

        with c1:
            new_prod = st.selectbox(
                "상품명",
                list(PRODUCTS.keys()),
                index=list(PRODUCTS.keys()).index(e["product"]),
                key=f"prod_{e['id']}",
                label_visibility="collapsed",
            )
            if new_prod != e["product"]:
                e["product"] = new_prod
                e["pay_year"] = PAY_YEARS.get(new_prod, ["기타"])[0]

        with c2:
            years_opt = PAY_YEARS.get(e["product"], ["기타"])
            e["pay_year"] = st.selectbox(
                "납입년도",
                years_opt,
                index=years_opt.index(e["pay_year"]),
                key=e["pay_year_key"],
                label_visibility="collapsed",
            )

        with c3:
            e["premium"] = currency_input(
                "월초 보험료(원)",
                key=e["premium_key"],
                default=e.get("premium", 0),
                label_visibility="collapsed",
            )

        with c4:
            if st.button("🗑 삭제", key=f"del_{e['id']}", use_container_width=True):
                remove_id = e["id"]
        st.markdown("")

    if remove_id is not None:
        st.session_state.entries = [x for x in st.session_state.entries if x["id"] != remove_id]

# ─────────────────────────────────────
# 계산 로직
# ─────────────────────────────────────
if st.button("📌 계산하기"):
    st.divider()
    summary_placeholder = st.container()

    # 유지율 보정 계수
    def retention_factor(user_rate: int, standard_rate):
        if standard_rate is None:
            return 1.0
        delta = user_rate - standard_rate
        # 1차년 수수료는 +우대 없음 / -5% 구간만 반영(요약표에서 적용)
        if delta >= 0:
            return 1.00
        elif delta > -5:
            return 0.85
        else:
            return 0.70

    # ▶▶ 성과수수료 지급률 테이블 (요청안 반영)
    def performance_rate_by_months(months: int, eff: float) -> float:
        """
        months: 위임 차월(1=1차월)
        eff   : 유효환산P
        반환  : 지급률(0.0~0.9), eff < 700,000 이면 0.0
        """
        if eff < 700_000:
            return 0.0

        # 금액 구간: 10M, 5M, 2M, 1M, 0.7M 이상
        if months <= 12:
            # 1~12차월
            if eff >= 10_000_000: return 0.75
            if eff >= 5_000_000:  return 0.72
            if eff >= 2_000_000:  return 0.70
            if eff >= 1_000_000:  return 0.60
            # eff >= 700_000
            return 0.35
        elif months <= 24:
            # 13~24차월
            if eff >= 10_000_000: return 0.80
            if eff >= 5_000_000:  return 0.77
            if eff >= 2_000_000:  return 0.75
            if eff >= 1_000_000:  return 0.65
            return 0.40
        elif months <= 36:
            # 25~36차월
            if eff >= 10_000_000: return 0.85
            if eff >= 5_000_000:  return 0.82
            if eff >= 2_000_000:  return 0.80
            if eff >= 1_000_000:  return 0.70
            return 0.45
        else:
            # 37차월 이상
            if eff >= 10_000_000: return 0.90
            if eff >= 5_000_000:  return 0.87
            if eff >= 2_000_000:  return 0.85
            if eff >= 1_000_000:  return 0.75
            return 0.50

    # 총 환산보험료(모집) 합산
    total_converted_raw = 0
    for e in st.session_state.entries:
        rate = PRODUCTS[e["product"]] / 100
        total_converted_raw += e["premium"] * rate

    # 유효환산P
    effective_converted = max(0, total_converted_raw - refund_p)

    # 모집 시점 위임차월
    today = datetime.today()
    contract_months = (today.year - year) * 12 + (today.month - month) + 1

    # 성과수수료 기준율(Rbase) — ※ 유효환산P·차월별 테이블로 산정
    base_rate_raw = performance_rate_by_months(contract_months, effective_converted)
    base_rate = base_rate_raw  # 이후 유지율/직도입 우대는 표기·산정 시 별도로 반영

    # 초기정착2 전제조건
    cond_std = bool(std_activity)
    cond_month = contract_months <= 12
    cond_amt_init2 = effective_converted >= 1_000_000
    eligible_init2 = cond_std and cond_month and cond_amt_init2

    # 초기정착2 최대지급률(모집 1~12차월 대상 = 75%)
    Rmax = 0.75
    delta_R_raw = max(0.0, Rmax - base_rate) if eligible_init2 else 0.0

    # 시점별 보정계수(요약/1차년은 -구간만, +우대 없음)
    _std_now_dynamic_calc = _std_retention(contract_months)
    f1  = retention_factor(retention_1st, _std_now_dynamic_calc)
    f13 = retention_factor(retention_13th, _std_13)  # 2차년 계산용
    f25 = retention_factor(retention_25th, _std_25)  # 3차년 계산용

    # 전략건강 보너스 단가 산정용 건수
    def strategic_count(premium: int) -> float:
        if premium >= 50_000:
            return 1.0
        elif premium >= 30_000:
            return 0.5
        return 0.0

    total_sh_count = 0.0
    for e in st.session_state.entries:
        if e["product"] in STRATEGIC_HEALTH:
            total_sh_count += strategic_count(e["premium"])

    def per_unit_bonus(cnt: float) -> int:
        if cnt >= 5:
            return 70_000
        elif cnt >= 3:
            return 60_000
        elif cnt >= 2:
            return 55_000
        elif cnt >= 1:
            return 50_000
        else:
            return 0

    sh_unit = per_unit_bonus(total_sh_count)

    # 상품별 계산
    results = []
    sum_recruit = sum_perf1 = sum_init2_1 = sum_sh_bonus = 0

    for e in st.session_state.entries:
        prod = e["product"]
        premium = e["premium"]
        pay_year = e["pay_year"]
        converted = premium * (PRODUCTS[prod] / 100)
        y1, y2, y3 = converted * 0.6, converted * 0.2, converted * 0.2

        # 직도입 우대(성과1 한정)
        if direct_recruits >= 3:
            dr_bonus = 0.15
        elif direct_recruits == 2:
            dr_bonus = 0.10
        elif direct_recruits == 1:
            dr_bonus = 0.05
        else:
            dr_bonus = 0.0

        # 성과수수료
        # 성과1: (base_rate * f1) + 직도입 우대(p) — 단, base_rate가 0이면 우대 미적용
        perf1_rate_effective = (base_rate * f1) + (dr_bonus if base_rate > 0 else 0.0)
        perf1 = y1 * perf1_rate_effective

        # 성과2/3: 유지율 보정만
        perf2 = y2 * base_rate * f13
        perf3 = y3 * base_rate * f25

        # 초기정착2
        init2_rate_effective_1 = delta_R_raw * f1
        init2_1 = y1 * init2_rate_effective_1
        init2_2 = y2 * (delta_R_raw * f13)
        init2_3 = y3 * (delta_R_raw * f25)

        # 유지수수료(월)
        retention1_amt = y2 / 12
        retention2_amt = y3 / 12

        # 전략건강
        this_count = (1.0 if premium >= 50_000 else (0.5 if premium >= 30_000 else 0.0)) if prod in STRATEGIC_HEALTH else 0.0
        sh_bonus = int(this_count * sh_unit) if prod in STRATEGIC_HEALTH else 0
        sh_tag = " <span style='color:#dc2626'>[전략건강]</span>" if prod in STRATEGIC_HEALTH else ""

        # 모집수수료(=1차년 환산 100%)
        recruit_fee = y1

        # 익월 항목별 누적
        sum_recruit   += recruit_fee
        sum_perf1     += perf1
        sum_init2_1   += init2_1
        sum_sh_bonus  += sh_bonus

        results.append({
            "prod": prod, "pay_year": pay_year, "premium": premium, "sh_tag": sh_tag,
            "recruit_fee": recruit_fee,
            "perf1": perf1, "perf2": perf2, "perf3": perf3,
            "init2_1": init2_1, "init2_2": init2_2, "init2_3": init2_3,
            "retention1_amt": retention1_amt, "retention2_amt": retention2_amt,
            "sh_bonus": sh_bonus,
        })

    # ▶ 정착보장 수수료
    def guarantee_amount_base(effP: int) -> int:
        if effP >= 5_000_000: return 5_000_000
        if effP >= 4_000_000: return 4_500_000
        if effP >= 3_000_000: return 4_000_000
        if effP >= 2_500_000: return 3_500_000
        if effP >= 2_000_000: return 3_000_000
        if effP >= 1_500_000: return 2_500_000
        if effP >= 1_000_000: return 1_500_000
        return 0

    base_guarantee = guarantee_amount_base(effective_converted)
    add_guarantee = 1_000_000 if direct_recruits == 1 else (2_000_000 if direct_recruits >= 2 else 0)
    final_guarantee = base_guarantee + add_guarantee

    # 대상조건(정착보장)
    cond_ret = (_std_now_dynamic is None) or (retention_1st >= _std_now_dynamic)
    eligible_settle = (contract_months <= 12) and std_activity and cond_ret and (final_guarantee > 0)

    # 제반수수료(환수 반영)
    base_comp = sum_recruit + sum_perf1 + sum_init2_1
    base_comp_after_refund = max(0, base_comp - refund_amt)

    settle_bonus = (final_guarantee - base_comp_after_refund) if eligible_settle else 0
    if settle_bonus < 0:
        settle_bonus = 0

    # ── 상단 요약
    with summary_placeholder:
        st.markdown("<div style='font-size:1.8rem; font-weight:700;'>📢당월 수수료 요약</div>", unsafe_allow_html=True)

        info_lines = [
            f"- **당월환산보험료**: {int(total_converted_raw):,}P",
            f"- **당월 예상 환수성적**: {int(refund_p):,}P",
            f"- **유효환산보험료**: {int(effective_converted):,}P",
            f"- **기준 유지율**: {('해당사항없음' if _std_now_dynamic is None else str(_std_now_dynamic)+'%')}",
            f"- **현재 유지율**: {retention_1st}%",
        ]

        # 성과 지급률(표시용)
        perf_rate_has_base = base_rate_raw > 0  # 유효환산 70만P 미만이면 False
        # 1차년(-구간만) 가감률 f1는 1.0/0.85/0.70
        perf_rate_display = base_rate_raw * f1
        perf_rate_pct = int(perf_rate_display * 100)

        # 캡션(영향 요소만) — 직도입 우대는 수식은 별도로 보여주되, base_rate가 0이면 표시 안함
        perf_caption_parts = []
        if perf_rate_has_base:
            if f1 != 1.0:
                perf_caption_parts.append(f"지급률 {int(base_rate_raw*100)}% × 유지율 가감 {int(f1*100)}%")
            # 직도입 우대 표시는 지급률이 0이 아닐 때만
            if direct_recruits >= 1:
                # 실제 지급률에는 +p가 반영되어 있지만, 캡션은 우대항 존재시만 표시
                if direct_recruits == 1: dr_txt = "5%p"
                elif direct_recruits == 2: dr_txt = "10%p"
                else: dr_txt = "15%p"
                # base_rate가 0일 때는 아예 표시하지 않음(요청사항)
                if base_rate_raw > 0:
                    if f1 != 1.0:
                        perf_caption_parts.append(f"+ 직도입우대 {dr_txt}")
                    else:
                        perf_caption_parts.append(f"지급률 {int(base_rate_raw*100)}% + 직도입우대 {dr_txt}")

        if perf_caption_parts:
            info_lines.append(f"- **성과수수료 지급률**: {perf_rate_pct}%  ( * " + " ".join(perf_caption_parts) + " )")
        else:
            info_lines.append(f"- **성과수수료 지급률**: {perf_rate_pct}%")

        # 초기정착2 지급률(표시용)
        init2_caption_parts = []
        if eligible_init2:
            init2_rate_display = delta_R_raw * f1
            init2_rate_pct = int(init2_rate_display * 100)
            if delta_R_raw > 0:
                if f1 != 1.0:
                    init2_caption_parts.append(f"지급률 {int(delta_R_raw*100)}% × 유지율 가감 {int(f1*100)}%")
                else:
                    # 영향 없으면 수식 생략
                    pass
            # base_rate가 75%로 이미 최대면 초기2 발생 없음 표기(이전 요청사항 반영)
            else:
                init2_caption_parts = []

            if init2_caption_parts:
                info_lines.append(f"- **초기정착수수료2 지급률**: {init2_rate_pct}%  ( * " + " ".join(init2_caption_parts) + " )")
            else:
                info_lines.append(f"- **초기정착수수료2 지급률**: {init2_rate_pct}%")
        else:
            info_lines.append(f"- **초기정착수수료2 지급률**: 0%")

        # 전략건강
        info_lines.append(f"- **전략건강판매 건수(단가)** : {total_sh_count:g}건({sh_unit:,}원)")

        # 정착보장수수료 보장금액 — 13차월 이상은 숨김
        if contract_months <= 12:
            if add_guarantee > 0:
                info_lines.append(f"- **정착보장수수료 보장금액**: {final_guarantee:,.0f}원 (* 직도입 +{add_guarantee//10000:,}만원)")
            else:
                info_lines.append(f"- **정착보장수수료 보장금액**: {final_guarantee:,.0f}원")

        st.info("  \n".join(info_lines))

        # 정착보장 비대상 사유(1~12차월에 한해 노출)
        if contract_months <= 12 and settle_bonus == 0:
            reasons_settle = []
            if final_guarantee == 0:
                reasons_settle.append("유효환산 구간 미달")
            if not std_activity:
                reasons_settle.append("표준활동 미달성")
            if (_std_now_dynamic is not None) and (retention_1st < _std_now_dynamic):
                reasons_settle.append("당월 유지율 기준 미달")
            if reasons_settle:
                st.markdown("**＊ 정착보장수수료 미산출 이유:** " + ", ".join(reasons_settle))

        # 초기정착2 비대상 사유(별도 노출)
        if not eligible_init2:
            reasons_i2 = []
            if not std_activity:
                reasons_i2.append("표준활동 미달성")
            if not cond_month:
                reasons_i2.append("위임 13차월 이상")
            if not cond_amt_init2:
                reasons_i2.append("유효환산 100만원 미만")
            if cond_month and cond_amt_init2 and base_rate_raw >= 0.75 and contract_months <= 12:
                reasons_i2.append("성과수수료 최대 지급률 달성 상태")
            if reasons_i2:
                st.markdown("**＊ 초기정착수수료2 미산출 이유:** " + ", ".join(reasons_i2))

        # 익월 요약
        st.markdown("<div style='font-size:1.8rem; font-weight:700; margin-top:8px;'>📢익월 예상 수수료</div>", unsafe_allow_html=True)
        lines = [
            f"- **모집수수료** : {sum_recruit:,.0f}원",
            f"- **성과수수료1** : {sum_perf1:,.0f}원",
            f"- **초기정착수수료2-1** : {sum_init2_1:,.0f}원",
            f"- **전략건강 보너스** : {sum_sh_bonus:,.0f}원",
        ]
        if contract_months <= 12:
            lines.append(f"- **정착보장 수수료** : {settle_bonus:,.0f}원")
        next_month_total = sum_recruit + sum_perf1 + sum_init2_1 + sum_sh_bonus + (settle_bonus if contract_months <= 12 else 0)
        lines.append(f"\n**총합 : {next_month_total:,.0f}원**")
        st.warning("\n".join(lines))

        SP(50)

    # ── 상품별 상세
    st.subheader("📆 상품별 예상 수수료 계산")
    for r in results:
        st.markdown("---")
        st.markdown(f"### ✅ {r['prod']}{r['sh_tag']}", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:1.05rem'><b>월초 보험료</b>: {r['premium']:,.0f}원</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:1.05rem'><b>납입년도</b>: {r['pay_year']}</div>", unsafe_allow_html=True)
        SP(10)

        st.markdown("#### 1차년(익월) 수수료")
        st.write(f"- 모집수수료 : {r['recruit_fee']:,.0f}원")
        st.write(f"- 성과수수료1 : {r['perf1']:,.0f}원")
        st.write(f"- 초기정착수수료2-1 : {r['init2_1']:,.0f}원")
        if r['sh_bonus'] > 0:
            st.write(f"- 전략건강 보너스 : {r['sh_bonus']:,.0f}원")

        st.markdown("#### 2차년 수수료")
        st.write(f"- 유지수수료1 (13~24회차 보험료 납입시): {r['retention1_amt']:,.0f}원")
        st.write(f"- 성과수수료2 : {r['perf2']:,.0f}원")
        st.write(f"- 초기정착수수료2-2 : {r['init2_2']:,.0f}원")

        st.markdown("#### 3차년 수수료")
        st.write(f"- 유지수수료2 (25~36회차 보험료 납입시): {r['retention2_amt']:,.0f}원")
        st.write(f"- 성과수수료3 : {r['perf3']:,.0f}원")
        st.write(f"- 초기정착수수료2-3 : {r['init2_3']:,.0f}원")

        SP(40)



        st.success("**✔️지급조건**\n\n**＊ 성과수수료 : 지급월 기준 환산가동인 자**\n\n**＊ 초기정착수수료2 : 지급월 기준 표준활동 달성 및 유효환산 100만P 이상인 자**")
