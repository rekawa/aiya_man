import streamlit as st
import pandas as pd
import os
from PIL import Image
from pandas.api.types import CategoricalDtype 
from datetime import datetime 

st.set_page_config(layout="wide")

# -------------------- 設定とパスワードの定義 --------------------
# 【重要】閲覧者全員に共有するパスワード
VIEWER_PASSWORD = '20050302' # 👈 このパスワードを従業員に共有！

# 【重要】編集者（店長など）だけが知るパスワード
EDITOR_PASSWORD = '20050302' 

DATA_FILE = 'item_list.csv'
KEIJIBAN_FILE = 'keijiban.csv'
KEIJIBAN_CATEGORIES = ['煮焼', '天フ', 'デザート', 'バック', '張物', 'キッチン共通', 'その他'] 

# 食器データの定義 (省略)
DISH_DATA = {
    'dish_01': {'name': '小鉢', 'photo': 'kobachi.png', 'locations': ['kobachi_1.png']},
    'dish_02': {'name': 'とんすい', 'photo': 'tonsui.png', 'locations': ['tonsui_1.png', 'tonsui_2.png']},
    'dish_03': {'name': '茶碗蒸し', 'photo': 'chawanmushi.png', 'locations': ['chawanmushi_1.png']},
}
# マップ画像ファイルの定義 (省略)
MAP_IMAGE_PATH = 'map.png'
TARE_AREA_PHOTO = 'tare_area.png'
HAIZEN_AREA_PHOTO = 'haizen_area.png'
KOME_MEN_AREA_PHOTO = 'kome_men_area.png'
NIAKI_AREA_PHOTO = 'niyaki_area.png'
TENHU_AREA_PHOTO = 'tenhu_area.png'
FUNA_AREA_PHOTO = 'funa_area.png'
DESSERT_AREA_PHOTO = 'dessert_area.png'
BACK_AREA_PHOTO = 'back_area.png'
HARIMONO_AREA_PHOTO = 'harimono_area.png'
IRIGUCHI_AREA_PHOTO = 'iriguchi_area.png'


# -------------------- セッションステートの初期化 --------------------
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'item_df' not in st.session_state:
    st.session_state.item_df = pd.DataFrame(columns=['食材名', '日付', 'カテゴリ']) 
if 'current_map_view' not in st.session_state:
    st.session_state.current_map_view = MAP_IMAGE_PATH
if 'selected_fair' not in st.session_state:
    st.session_state.selected_fair = '全て表示'
if 'is_editor' not in st.session_state:
    st.session_state.is_editor = False 
if 'selected_dish_id' not in st.session_state:
    st.session_state.selected_dish_id = None 
if 'is_authenticated' not in st.session_state:
    st.session_state.is_authenticated = False # 👈 全体アクセス認証の状態を記憶

# -------------------- データ読み込み関数 --------------------
def load_data():
    """食材データを読み込む"""
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if 'カテゴリ' not in df.columns:
            df['カテゴリ'] = '年中' 
        st.session_state.item_df = df
    else:
        st.session_state.item_df = pd.DataFrame(columns=['食材名', '日付', 'カテゴリ']) 

def load_keijiban_data():
    """掲示板データを読み込む"""
    if os.path.exists(KEIJIBAN_FILE):
        df = pd.read_csv(KEIJIBAN_FILE)
    else:
        df = pd.DataFrame(columns=['日付', 'カテゴリ', '内容'])
    return df

# -------------------- UIパーツのコンポーネント関数 --------------------
# (既存の show_home, show_keijiban, show_dish_guide, show_food_date_manager, show_kitchen_map, show_delete_tool 関数はそのまま使用します)

def show_home():
    st.header('トップメニュー')
    st.write('このアプリは、新人アルバイトのためのデジタルマニュアルです。')
    st.write('左上のメニューから、利用したいシステムを選択してください。')

def show_keijiban():
    st.header('💡 掲示板')
    st.write('従業員が実際に感じた危険な出来事を共有し、店舗全体の安全意識を高めましょう。')
    
    with st.expander("新しく投稿する", expanded=False):
        category = st.selectbox('カテゴリーを選択', KEIJIBAN_CATEGORIES, key='keijiban_category_select')
        content = st.text_area('内容を記述してください', key='keijiban_content_area')
        
        if st.button('投稿する', type='primary'):
            if content:
                post_date = datetime.now().strftime('%Y/%m/%d %H:%M') 
                new_post = pd.DataFrame([{'日付': post_date, 'カテゴリ': category, '内容': content}])
                current_keijiban_df = load_keijiban_data()
                updated_df = pd.concat([current_keijiban_df, new_post], ignore_index=True)
                updated_df.to_csv(KEIJIBAN_FILE, index=False)
                st.success("投稿されました。ご協力ありがとうございます！")
                st.rerun() 
            else:
                st.warning("内容を入力してください。")
                
    st.markdown('---')
    st.subheader('過去の投稿一覧')
    
    keijiban_df = load_keijiban_data()
    if keijiban_df.empty:
        st.info("まだ投稿はありません。")
        return

    filter_options = ['全てのカテゴリー'] + KEIJIBAN_CATEGORIES
    selected_filter = st.selectbox('表示するカテゴリーで絞り込む', filter_options, key='keijiban_filter')
    df_to_display = keijiban_df.copy()
    
    if selected_filter != '全てのカテゴリー':
        df_to_display = df_to_display[df_to_display['カテゴリ'] == selected_filter]
        
    df_to_display = df_to_display.sort_values(by='日付', ascending=False)
    
    if not df_to_display.empty:
        st.dataframe(df_to_display, use_container_width=True)
    else:
        st.info(f"【{selected_filter}】の投稿は見つかりませんでした。")

def show_dish_guide():
    st.header('🍽️ 食器の定位置ガイド')
    if st.session_state.selected_dish_id:
        dish_id = st.session_state.selected_dish_id
        dish_info = DISH_DATA[dish_id]
        st.subheader(f'【{dish_info["name"]}】の定位置')
        for i, location_path in enumerate(dish_info['locations']):
            st.markdown(f'#### 定位置 {i + 1}')
            try:
                st.image(Image.open(location_path), caption=f'{dish_info["name"]}の保管場所', use_column_width=True)
            except FileNotFoundError:
                st.error(f"エラー: 定位置画像ファイルが見つかりません: {location_path}")
        if st.button('一覧に戻る', key='back_to_dish_list', type='secondary'):
            st.session_state.selected_dish_id = None
            st.rerun()
    else:
        st.write("定位置を調べたい食器を選んでください。")
        cols = st.columns(3)
        dish_ids = list(DISH_DATA.keys())
        for i, dish_id in enumerate(dish_ids):
            dish_info = DISH_DATA[dish_id]
            with cols[i % 3]: 
                st.markdown(f"**{dish_info['name']}**")
                try:
                    st.image(Image.open(dish_info['photo']), width=150)
                except FileNotFoundError:
                    st.error(f"エラー: 食器画像が見つかりません: {dish_info['photo']}")
                if st.button('定位置を確認', key=f'select_{dish_id}'):
                    st.session_state.selected_dish_id = dish_id
                    st.rerun()

def show_food_date_manager():
    st.header('食材の日付管理システム')
    if st.session_state.is_editor:
        with st.expander("新しい食材を登録する", expanded=False): 
            food_name = st.text_input('食材の名前を入力してください')
            date_options = ['日付なし', '当日', '翌日']
            for i in range(2, 7):
                date_options.append(f'{i}日後')
            selected_day = st.selectbox('日付を選択してください', date_options)
            category_options = ['年中', 'フェア9月〜', 'フェア10月〜', 'フェア11月〜', 'その他']
            selected_category = st.selectbox('カテゴリを選択してください', category_options)
            if st.button('リストに追加', type='primary'):
                if food_name:
                    new_item = pd.DataFrame([{'食材名': food_name, '日付': selected_day, 'カテゴリ': selected_category}])
                    updated_df = pd.concat([st.session_state.item_df, new_item], ignore_index=True)
                    updated_df.to_csv(DATA_FILE, index=False)
                    st.success(f'{food_name}（{selected_category}）がリストに追加されました！')
                    st.rerun()
                else:
                    st.warning('食材の名前を入力してください！')
    else:
        st.info("新しい食材の登録は、編集権限を持つユーザー（店長など）のみが行えます。サイドバーからログインしてください。")
    st.markdown('---')
    st.subheader('登録済みリスト')
    current_df = st.session_state.item_df.copy()
    fair_categories = current_df['カテゴリ'].unique().tolist()
    fair_categories = [c for c in fair_categories if c != '年中']
    filter_options = ['全て表示'] + sorted(fair_categories) 
    selected_filter = st.selectbox('表示するフェアを選択', filter_options, key='fair_filter')
    df_nenju = current_df[current_df['カテゴリ'] == '年中']
    if selected_filter == '全て表示':
        df_fair = current_df[current_df['カテゴリ'] != '年中']
    else:
        df_fair = current_df[current_df['カテゴリ'] == selected_filter]
    df_to_display = pd.concat([df_nenju, df_fair], ignore_index=True)
    st.write(f"**表示中のカテゴリ**: {selected_filter if selected_filter != '全て表示' else '全て'}")
    if not df_to_display.empty:
        custom_date_order = ['当日', '翌日', '2日後', '3日後', '4日後', '5日後', '6日後', '日付なし']
        date_category_type = CategoricalDtype(categories=custom_date_order, ordered=True)
        df_to_display['日付'] = df_to_display['日付'].astype(date_category_type)
        df_to_display = df_to_display.sort_values(by=['日付', 'カテゴリ'], ascending=[True, True])
        df_to_display['日付'] = df_to_display['日付'].astype(str)
        st.dataframe(df_to_display)
    else:
        st.info("該当する食材が登録されていません。")

def show_kitchen_map():
    st.header('厨房マップ')
    if st.session_state.current_map_view == MAP_IMAGE_PATH:
        try:
            st.image(Image.open(MAP_IMAGE_PATH), caption='厨房の全体図', use_column_width=True)
        except FileNotFoundError:
            st.error(f"エラー: マップ画像ファイルが見つかりません: {MAP_IMAGE_PATH}")
        st.write("ボタンを押して、それぞれの場所から見える景色を確認してください:")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            if st.button('タレ', key='tare_area_button'): st.session_state.current_map_view = TARE_AREA_PHOTO; st.rerun()
        with col2:
            if st.button('配膳', key='haizen_area_button'): st.session_state.current_map_view = HAIZEN_AREA_PHOTO; st.rerun()
        with col3:
            if st.button('米・麺', key='kome_men_area_button'): st.session_state.current_map_view = KOME_MEN_AREA_PHOTO; st.rerun()
        with col4:
            if st.button('煮焼', key='niyaki_area_button'): st.session_state.current_map_view = NIAKI_AREA_PHOTO; st.rerun()
        with col5:
            if st.button('天フ', key='tenhu_area_button'): st.session_state.current_map_view = TENHU_AREA_PHOTO; st.rerun()
        col6, col7, col8, col9, col10 = st.columns(5)
        with col6:
            if st.button('舟', key='funa_area_button'): st.session_state.current_map_view = FUNA_AREA_PHOTO; st.rerun()
        with col7:
            if st.button('デザート', key='dessert_area_button'): st.session_state.current_map_view = DESSERT_AREA_PHOTO; st.rerun()
        with col8:
            if st.button('バック', key='back_area_button'): st.session_state.current_map_view = BACK_AREA_PHOTO; st.rerun()
        with col9:
            if st.button('張物', key='harimono_area_button'): st.session_state.current_map_view = HARIMONO_AREA_PHOTO; st.rerun()
        with col10:
            if st.button('入口', key='iriguchi_area_button'): st.session_state.current_map_view = IRIGUCHI_AREA_PHOTO; st.rerun()
    else:
        try:
            detail_photo = Image.open(st.session_state.current_map_view)
            st.image(detail_photo, use_column_width=True)
        except FileNotFoundError:
            st.error("エラー: 詳細画像ファイルが見つかりません。")
        if st.button('全体マップに戻る', type='secondary'):
            st.session_state.current_map_view = MAP_IMAGE_PATH
            st.rerun()

def show_delete_tool():
    st.header('登録データ削除')
    if st.session_state.is_editor:
        item_df = st.session_state.item_df
        if not item_df.empty:
            st.dataframe(item_df)
            st.write('---')
            index_to_delete = st.selectbox('削除したい項目の番号を選択してください', item_df.index)
            if st.button('削除を実行'):
                updated_df = item_df.drop(index_to_delete).reset_index(drop=True)
                updated_df.to_csv(DATA_FILE, index=False)
                st.success("項目が削除されました。")
                st.session_state.item_df = updated_df
                st.rerun()
        else:
            st.info("削除できる項目はありません。")
    else:
        st.warning("この機能は編集権限を持つユーザー（店長など）のみ利用できます。")


# -------------------- メインロジック --------------------
load_data()

# メイン表示が認証済みかどうかで分岐
if not st.session_state.is_authenticated:
    st.title("店舗デジタルマニュアル")
    st.markdown('---')
    st.subheader('🔒 アクセス認証が必要です')
    st.write('このアプリは機密情報を含むため、閲覧にはパスワードが必要です。')
    
    password_input = st.text_input('店舗アクセスパスワードを入力', type='password', key='viewer_auth')
    
    if st.button('サイトにアクセス', key='auth_button'):
        if password_input == VIEWER_PASSWORD:
            st.session_state.is_authenticated = True
            # パスワードが正しい場合、編集権限をリセットしてトップページへ移動
            st.session_state.is_editor = False 
            st.rerun()
        else:
            st.error('パスワードが違います。従業員にご確認ください。')
else:
    # 認証済みの場合、通常のアプリ表示ロジックを実行
    
    # サイドバーにメニューボタンとログインUIを配置
    with st.sidebar:
        st.header('メニュー')
        
        # ログインUI
        st.markdown('---')
        st.subheader('🔑 編集者ログイン')
        
        if st.session_state.is_editor:
            st.success('編集者としてログイン中')
            if st.button('ログアウト', key='logout_button'):
                st.session_state.is_editor = False
                st.rerun()
        else:
            password_input = st.text_input('パスワードを入力', type='password', key='editor_login')
            if st.button('ログイン', key='editor_login_button'):
                if password_input == EDITOR_PASSWORD:
                    st.session_state.is_editor = True
                    st.rerun()
                else:
                    st.error('パスワードが違います')
        st.markdown('---')

        # ナビゲーションボタン
        if st.button('トップへ', key='home_button'):
            st.session_state.page = 'home'
            st.session_state.current_map_view = MAP_IMAGE_PATH
            st.rerun()
        if st.button('食材の日付', key='food_date_button'):
            st.session_state.page = 'food_date'
            st.session_state.current_map_view = MAP_IMAGE_PATH
            st.rerun()
        if st.button('食器ガイド', key='dish_guide_button'):
            st.session_state.page = 'dish_guide'
            st.session_state.current_map_view = MAP_IMAGE_PATH
            st.rerun()
        if st.button('掲示板', key='keijiban_button'): 
            st.session_state.page = 'keijiban'
            st.session_state.current_map_view = MAP_IMAGE_PATH
            st.rerun()
        if st.button('厨房マップ', key='kitchen_map_button'):
            st.session_state.page = 'kitchen_map'
            st.session_state.current_map_view = MAP_IMAGE_PATH
            st.rerun()
        if st.button('登録データ削除', key='delete_tool_button'):
            st.session_state.page = 'delete_tool'
            st.session_state.current_map_view = MAP_IMAGE_PATH
            st.rerun()

    # ページごとの表示を制御
    if st.session_state.page == 'home':
        show_home()
    elif st.session_state.page == 'food_date':
        show_food_date_manager()
    elif st.session_state.page == 'dish_guide': 
        show_dish_guide()
    elif st.session_state.page == 'keijiban': 
        show_keijiban()
    elif st.session_state.page == 'kitchen_map':
        show_kitchen_map()
    elif st.session_state.page == 'delete_tool':
        show_delete_tool()