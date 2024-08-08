import streamlit as st
import datetime
import requests
import numpy as np
from openai import OpenAI
from PIL import Image
import re
from geopy.distance import geodesic

st.set_page_config(layout="wide")

# 사이드바 - 이용 가이드
with st.sidebar:   
    img_url = 'https://i.ibb.co/XyMD4m0/logo4.png'
    st.image(img_url, width=150)
    st.write("사용을 위하여 openai key를 입력하세요")
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
    st.subheader("**서비스 이용 가이드**")
    st.markdown(":red[***STEP1***] 서울메이트에게 반갑게 인사해주세요:hand:")
    st.markdown(":red[***STEP2***] 원하는 여행 테마를 입력하세요")
    st.markdown(":red[***STEP3***] 방문하고 싶은 지역을 선택하세요")
    st.markdown(":red[***STEP4***] 추천 여행지로 이루어진 경로생성이 완성되었어요!") 
    st.subheader("**이용 TIP**:sunglasses:")
    st.markdown("*1.* 여행지가 마음에 들지 않는다면 다시 물어볼 수 있어요!")
    st.markdown("*2.* 서비스를 여러 번 이용하면 n박 여행 계획을 세울 수 있어요!")

st.title("Seoul Mate")

# expander
with st.expander('만든 이에 대하여'):
  st.markdown(
      """저희는 네 명의 고려대학교 재학생으로 이루어진 이^3조입니다.
    """
  )

if not openai_api_key:
    st.info("서비스를 사용하려면 openai key를 입력하세요", icon="🗝️")
else:
    client = OpenAI(api_key=openai_api_key)

    city = "\n강남구\n 강동구\n 강북구\n 강서구\n 관악구\n 광진구\n 구로구\n 금천구\n 노원구\n 도봉구\n 동대문구\n 동작구\n 마포구\n 서대문구\n 서초구\n 성동구\n 성북구\n 송파구\n 양천구\n 영등포구\n 용산구\n 은평구\n 종로구\n 중구\n 중랑구\n"
    date = st.date_input("여행 날짜를 입력하고 메이트에게 인사해보세요!")
    date_str = date.strftime("%Y년 %m월 %d일")
    theme = "\n워케이션\n 미술관 탐방\n 자연과 휴식\n 맛집 탐방\n 한류를 따라서\n 전통과 역사 속으로\n 쇼핑\n 액티비티와 스포츠\n 무더운 여름 시원하게 나기\n 반려동물과 함께\n 대학가 탐방\n 전통 시장 탐방\n"

    # st.session_state 초기화
    if "step" not in st.session_state:
        st.session_state.step = 1
    if "messages" not in st.session_state:
        st.session_state.messages = []


    # 테마 질문
    system_message_theme = {
        "role": "system",
        "content": (
            "너는 사용자에게 질문하면서 사용자가 하루동안 서울 여행 계획을 도와주는 친절한 조수야."
            "내가 테마 목록을 줄거야. 그중 사용자가 관심있는 테마들을 선택할 수 있도록 질문해줘."
            "테마는 다음과 같아" + theme + "원하는 테마가 없다면 사용자가 직접 입력해도 괜찮아"
            "테마에 대한 사용자의 답변을 참고해서 여행지와 관련된 핵심 키워드를 총 7개 추출해줘. "
            "단, 질문할 때는 내가 제공하는 질문만 하고, 키워드에 대해서는 언급하지 말아줘"
            "키워드 추출은 꼭 영어로 해줘. "
            "키워드는 다음과 같은 형식으로 추출해줘. 다른 부연설명은 하지마. ex) 1. university student 2. campus 3. cozy cafes\n\n"
            "추가 정보에 대한 질문은 절대 하지마."
        )
    }


    # 자치구 질문
    system_message_city = {
        "role": "system",
        "content": (
            "내가 서울시 자치구 목록을 줄거야. 그 중 사용자가 방문하고 싶은 자치구 하나만 선택할 수 있도록 질문해줘."
            "자치구 목록은 다음과 같아" + city +
            "자치구 목록을 한 줄에 5개씩 나열해서 보여줘 ex) 강남구 강동구 강북구 강서구 관악구\n강남구 강동구 강북구 강서구 관악구\n"
            "사용자의 답변을 받고 다음과 같은 형식으로 추출해줘 ex) *강남구*\n\n"
            "추가 정보에 대한 질문은 절대 하지마."
        )
    }


    if st.button("RESTART"):
        st.session_state.messages = []
        st.session_state.step = 1


    if not st.session_state.messages or st.session_state.messages[0]["role"] != "system":
        st.session_state.messages.insert(0, system_message_theme)

    # 시스템 메시지 이외 주고 받는 메시지를 화면에 표시
    for message in st.session_state.messages[1:]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


    # 메시지 입력창
    if prompt := st.chat_input("질문에 대답해주세요!"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 첫 번째 단계: 테마 질문
        if st.session_state.step == 1:
            response1 = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages,
            )
            assistant_reply1 = response1.choices[0].message.content

            st.session_state.messages.append({"role": "assistant", "content": assistant_reply1})
            with st.chat_message("assistant"):
                st.markdown(assistant_reply1)

            # 키워드 추출
            keywords = re.findall(r'\d+\.\s(.*?)\s*(?=\d+\.|$)', assistant_reply1, re.DOTALL)
            keywords_list = list(map(str.strip, keywords))
            keywords_str = ", ".join(keywords_list)

            print("keywords: ", keywords_str)
            st.session_state.key = keywords_str
            print(st.session_state.key)

            if len(keywords_list) >= 5 and len(keywords_list) <=10:
                st.session_state.step = 2


    # 다음 버튼 표시
    if st.session_state.get("step") == 2 and st.button("지역 선택"):
        st.session_state.messages.insert(0, system_message_city)
        st.session_state.step = 3


    # 두 번째 단계: 도시 질문
    if st.session_state.step == 3:
        response2 = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=st.session_state.messages,
        )
        assistant_reply2 = response2.choices[0].message.content

        st.session_state.messages.append({"role": "assistant", "content": assistant_reply2})
        with st.chat_message("assistant"):
            st.markdown(assistant_reply2)

        # 자치구 str 추출
        city_selected = re.findall(r'\*(.*?)\*', assistant_reply2)
        city_str = ",".join(city_selected)

        print("selected cities:", city_str)
        st.session_state.city = city_str.replace(" ","")
        
        region = {'강남구':'37.517305,127.047502','강동구':'37.530126,127.1237708','강북구':'37.6397819,127.0256135','강서구':'37.550937,126.849642','관악구':'37.4781549,126.9514847',
                '광진구':'37.538617,127.082375','구로구':'37.495472,126.887536','금천구':'37.4568644,126.8955105','노원구':'37.654358,127.056473','도봉구':'37.668768,127.047163',
                '동대문구':'37.574524,127.03965','동작구':'37.51245,126.9395','마포구':'37.5663245,126.901491','서대문구':'37.579225,126.9368','서초구':'37.483569,127.032598',
                '성동구':'37.563456,127.036821','성북구':'37.5894,127.016749','송파구':'37.5145636,127.1059186','양천구':'37.517016,126.866642','영등포구':'37.526436,126.896004',
                '용산구':'37.532527,126.99049','은평구':'37.602784,126.929164','종로구':'37.5735207,126.9788345','중구':'37.563843,126.997602','중랑구':'37.6063242,127.0925842'}
        
        #장소 추출 함수
        def get_places(api_key, theme, location, radius=1000):
            endpoint_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
                # 파라미터 설정
            params = {
                'query': theme,
                'location': location,
                'radius': radius,
                'key': api_key,
                'language': 'ko',
            }
            response = requests.get(endpoint_url, params=params)
            results = response.json().get('results', [])
            # 장소 리스트 생성
            places = []
            origin_lat, origin_lng = map(float, location.split(','))
            origin_coords = (origin_lat, origin_lng)
            for place in results[:100]:
                place_lat = place['geometry']['location']['lat']
                place_lng = place['geometry']['location']['lng']
                place_coords = (place_lat, place_lng)
                distance = geodesic(origin_coords, place_coords).kilometers
                if place['rating'] and (place['user_ratings_total'] > 10) and (distance <= 10) and ('restaurant' not in place['types']):   #리뷰 개수 10개 이상만
                    name = place.get('name')
                    address = place.get('formatted_address')
                    rating = place.get('rating')
                    total = place.get('user_ratings_total')
                    lng = place.get('geometry').get('location').get('lng')
                    lat = place.get('geometry').get('location').get('lat')
                    loc = (lat,lng)
                    types = place.get('types')
                    places.append({
                    'name': name,
                    'address': address,
                    'rating': rating,
                    'total' : total,
                    'loc' : loc,
                    'dist' : distance,
                    'types' : types
                })
            return places
    
        def get_restaurants(api_key, theme, location, radius=1000):
            endpoint_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

            # 파라미터 설정
            params = {
                'query': theme,
                'location': location,
                'radius': radius,
                'key': api_key,
                'language': 'ko',
            }

            response = requests.get(endpoint_url, params=params)
            results = response.json().get('results', [])

        # 장소 리스트 생성
            places = []
            origin_lat, origin_lng = map(float, location.split(','))
            origin_coords = (origin_lat, origin_lng)
            for place in results[:100]:
                place_lat = place['geometry']['location']['lat']
                place_lng = place['geometry']['location']['lng']
                place_coords = (place_lat, place_lng)
                distance = geodesic(origin_coords, place_coords).kilometers
                if place['rating'] and (place['user_ratings_total'] > 10) and (distance <= 10):   #리뷰 개수 10개 이상만
                    name = place.get('name')
                    address = place.get('formatted_address')
                    rating = place.get('rating')
                    total = place.get('user_ratings_total')
                    lng = place.get('geometry').get('location').get('lng')
                    lat = place.get('geometry').get('location').get('lat')
                    loc = (lat,lng)
                    types = place.get('types')
                    places.append({
                        'name': name,
                        'address': address,
                        'rating': rating,
                        'total' : total,
                        'loc' : loc,
                        'dist' : distance,
                        'types' : types
                    })
            return places
    

        def get_place_id(api_key, place_name, location):
            url = 'https://maps.googleapis.com/maps/api/place/findplacefromtext/json'
            params = {
                'input': place_name,
                'inputtype': 'textquery',
                'fields': 'place_id',
                'locationbias': f'point:{location}',
                'key': api_key
            }
            response = requests.get(url, params=params)
            place_id = response.json()['candidates'][0]['place_id']
            return place_id

            # 장소의 세부 정보를 얻어오는 함수
        def get_place_details(api_key, place_id):
            url = 'https://maps.googleapis.com/maps/api/place/details/json'
            params = {
                'place_id': place_id,
                'fields': 'name,rating,formatted_address,photo',
                'key': api_key
            }
            response = requests.get(url, params=params)
            return response.json()

        # 사진의 URL을 얻어오는 함수
        def get_photo_url(api_key, photo_reference):
            return f'https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={api_key}'

        # 메인 함수
        def return_url(place_name, location, API_KEY):
            place_id = get_place_id(API_KEY, place_name, location)
            place_details = get_place_details(API_KEY, place_id)

            # 사진 참조가 있는지 확인
            if 'photos' in place_details['result']:
                photo_reference = place_details['result']['photos'][0]['photo_reference']
                photo_url = get_photo_url(API_KEY, photo_reference)
                return photo_url

        # 사용자 입력
        theme = st.session_state.get("key").split(',')
        location = region.get(st.session_state.get("city"))

        # API 키 입력
        api_key = 'AIzaSyDrh43CtyY57-b30HT6cPZ4bjSRtHrbE_s'

        #키워드별 장소 추출 및 중복 장소 제거
        places = []
        idx = 0
        if theme and location:
            while True:
                data = get_places(api_key, theme[idx], location)
                if data:
                    r = np.random.choice(data, min(2,len(data)), replace = False)
                    r = list(r)
                    if r not in places:
                        places += r
                idx += 1
                if idx == len(theme) : idx = 0
                if len(places) == 10: break

        #식당 추출 및 랜덤하게 2개 선택
        if location:
            restaurants = get_restaurants(api_key, 'restaurant for lunch and dinner', location)
            random_restaurants = np.random.choice(restaurants, 2, replace=False)
            random_restaurants = list(random_restaurants)
            chosen_places = np.random.choice(places, 5, replace=False)
            chosen_places = list(chosen_places)
            chosen_places += random_restaurants

    # 결과 출력
            for idx, place in enumerate(places):
                #place_names.append(place['name'])
                print(f"{idx+1}. {place['name']}")
                print(f"   주소: {place['address']}")
                print(f"   평점: {place['rating']}")
                print(f"   리뷰 개수 : {place['total']}")
                print(f"   종류 : {place['types']}")
                print(f"   좌표 : {place['loc']}")
                print(f"   거리 : {place['dist']}")
            print()
            for idx, place in enumerate(random_restaurants):
                print(f"{idx+1}. {place['name']}")
                print(f"   주소: {place['address']}")
                print(f"   평점: {place['rating']}")
                print(f"   리뷰 개수 : {place['total']}")
                print(f"   종류 : {place['types']}")
                print(f"   좌표 : {place['loc']}")
                print(f"   거리 : {place['dist']}")

            col1, col2, col3, col4, col5= st.columns(5)
            st.markdown("""
                <style>
                    .header {
                    font-size: 18px; /* 원하는 폰트 크기로 조정 */
                }
                </style>
                """, unsafe_allow_html=True)
            with col1:
                st.markdown(f'<h1 class="header">{chosen_places[0]['name']}</h1>', unsafe_allow_html=True)
                st.image(return_url(chosen_places[0]['name'],chosen_places[0]['loc'],api_key))
            with col2:
                st.markdown(f'<h1 class="header">{chosen_places[1]['name']}</h1>', unsafe_allow_html=True)
                st.image(return_url(chosen_places[1]['name'],chosen_places[1]['loc'],api_key))
            with col3:
                st.markdown(f'<h1 class="header">{chosen_places[2]['name']}</h1>', unsafe_allow_html=True)
                st.image(return_url(chosen_places[2]['name'],chosen_places[2]['loc'],api_key))
            with col4:
                st.markdown(f'<h1 class="header">{chosen_places[3]['name']}</h1>', unsafe_allow_html=True)
                st.image(return_url(chosen_places[3]['name'],chosen_places[3]['loc'],api_key))
            with col5:
                st.markdown(f'<h1 class="header">{chosen_places[4]['name']}</h1>', unsafe_allow_html=True)
                st.image(return_url(chosen_places[4]['name'],chosen_places[4]['loc'],api_key))
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f'<h1 class="header">{chosen_places[5]['name']}</h1>', unsafe_allow_html=True)
                st.image(return_url(chosen_places[5]['name'],chosen_places[5]['loc'],api_key), width = 200)
            with col2:
                st.markdown(f'<h1 class="header">{chosen_places[6]['name']}</h1>', unsafe_allow_html=True)
                st.image(return_url(chosen_places[6]['name'],chosen_places[6]['loc'],api_key), width = 200)
            
            visit_dict = dict()
            for i in chosen_places:
                visit_dict[i['name']] = i['loc']
            print(visit_dict)
