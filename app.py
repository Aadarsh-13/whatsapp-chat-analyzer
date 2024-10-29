from collections import Counter
from urlextract import URLExtract
extract = URLExtract()
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import datetime
import time
import re
import pandas as pd
import emoji

################################################ preprocess
def preprocess(data):
    pattern = '\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s-\s'

    messages = re.split(pattern, data)[1:]
    dates = re.findall(pattern, data)

    df = pd.DataFrame({'user_message': messages, 'message_date': dates})
    df['message_date'] = pd.to_datetime(df['message_date'], format='%m/%d/%y, %H:%M - ')
    df.rename(columns={'message_date': 'date'}, inplace=True)

    users = []
    messages = []
    for message in df['user_message']:
        entry = re.split('([\w\W]+?):\s', message)
        if entry[1:]:  # user name
            users.append(entry[1])
            messages.append(entry[2])
        else:
            users.append('group notification')
            messages.append(entry[0])

    df['user'] = users
    df['message'] = messages
    df.drop(columns=['user_message'], inplace=True)

    df['only_date'] = df['date'].dt.date
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute

    period = []
    for hour in df[['day_name', 'hour']]['hour']:
        if hour == 23:
            period.append(str(hour) + "-" + str('00'))
        elif hour == 0:
            period.append(str('00') + "-" + str(hour + 1))
        else:
            period.append(str(hour) + "-" + str(hour + 1))
    df['period'] = period
    return df

################################################3helper
def fatch_stats(selected_user, df):
    if selected_user != 'overall':
        df = df[df['user'] == selected_user]

    # fatch the number of message

    num_message = df.shape[0]

    # fatch the total number of words

    words = []
    for message in df['message']:
        words.extend(message.split())

    # fatch the midia
    num_media_message = df[df['message'] == '<Media omitted>\n'].shape[0]

    # fatch number of links shared
    links = []
    for message in df['message']:
        links.extend(extract.find_urls(message))

    return num_message, len(words), num_media_message, len(links)

########## most busy user
def most_busy_Users(df):
    x = df['user'].value_counts().head()
    df = round((df['user'].value_counts() / df.shape[0]) * 100, 2).reset_index().rename(
        columns={'index': 'name', 'user': 'percent'})
    return x, df

#MOST COMMON WORDS HELPER

def most_common_words(selected_user, df):
    f = open('stop_hinglish.txt', 'r')
    stop_words = f.read()

    if selected_user != 'overall':
        df = df[df['user'] == selected_user]

    temp = df[df['user'] != 'group notification']
    temp = temp[temp['message'] != '<Media omitted>\n']

    words = []

    for message in temp['message']:
        for word in message.lower().split():
            if word not in stop_words:
                words.append(word)
    most_common_df = pd.DataFrame(Counter(words).most_common(20))
    return most_common_df

# emoji helper
def emoji_helper(selected_user, df):
    if selected_user != 'overall':
        df = df[df['user'] == selected_user]
    emojis = []
    for message in df['message']:
        emojis.extend([C for C in message if C in emoji.EMOJI_DATA])
    emoji_df = pd.DataFrame(Counter(emojis).most_common(len(Counter(emojis))))

    return emoji_df

# monthely timeline
def monthly_timline(selected_user, df):
    if selected_user != 'overall':
        df = df[df['user'] == selected_user]
    timeline = df.groupby(['year', 'month_num', 'month']).count()['message'].reset_index()
    time = []
    for i in range(timeline.shape[0]):
        time.append(timeline['month'][i] + "-" + str(timeline['year'][i]))
    timeline['time'] = time
    return timeline


def daily_timeline(selected_user, df):
    if selected_user != 'overall':
        df = df[df['user'] == selected_user]
    daily_timeline = df.groupby('only_date').count()['message'].reset_index()
    return daily_timeline


def week_activity_map(selected_user, df):
    if selected_user != 'overall':
        df = df[df['user'] == selected_user]
    return df['day_name'].value_counts()


def month_activity_map(selected_user, df):
    if selected_user != 'overall':
        df = df[df['user'] == selected_user]
    return df['month'].value_counts()


def activity_heatmap(selected_user, df):
    if selected_user != 'overall':
        df = df[df['user'] == selected_user]
    user_heatmap = df.pivot_table(index='day_name', columns='period', values='message', aggfunc='count').fillna(0)
    return user_heatmap


########################################################################### when program run first interface

############# background image
def add_bg_from_url():
    st.markdown(
        f"""
           <style>
           .stApp {{
               background-image: url("https://w0.peakpx.com/wallpaper/1020/46/HD-wallpaper-whatsapp-cartoon-random-skull-simple-dark-black.jpg");
               background-attachment: fixed;
               background-size: cover
           }}
           </style>
           """,
        unsafe_allow_html=True
    )

add_bg_from_url()
########################sidebar image
def main():
    st.sidebar.image("https://img.lovepik.com/photo/40036/7999.jpg_wh300.jpg", use_column_width=True)

main()

st.sidebar.title("whatsapp chat analyzer")
uploaded_file = st.sidebar.file_uploader("Choose a file")
if uploaded_file is not None:
    # To read file as bytes:
    bytes_data = uploaded_file.getvalue()
    data = bytes_data.decode("Utf-8")
    df = preprocess(data)


    def add_bg_from_url():
        st.markdown(
            f"""
               <style>
               .stApp {{
                   background-image: url("https://images.squarespace-cdn.com/content/v1/5cb06a6cd7456246c1156693/1583858428838-08JDDER1VRLWJWYUIX28/IMG_0246.JPG");
                   background-attachment: fixed;
                   background-size: cover
               }}
               </style>
               """,
            unsafe_allow_html=True
        )
    add_bg_from_url()


# ##################################################### app main part after show analysis

    # fatch unique users
    user_list = df['user'].unique().tolist()

    user_list.sort()
    user_list.insert(0, "overall")

    selected_user = st.sidebar.selectbox("show analysis with respect to ", user_list)

################### spninner
    def a1():
        with st.spinner('Please wait a second...'):
            time.sleep((3))
            st.success('File selected  successfully')


    def a2():
        a1 = st.text_input("Enter  the Key   ")
        ENTER = st.button('ENTER')
        if ENTER:
            if 'ADARSH13' in a1:
                st.success("SUCCESS")
                st.dataframe(df)
            else:
                st.error("error ")
                st.warning(
                    "warning warning warning !!!!!!!!!!!!!!!!!!!!!! the system call 100")

                st.exception(" data will be locked")
                st.help()
                st.stop()

        ############## for experiment


    def a3():
        st.date_input('Today is ', datetime.datetime.now())
        st.time_input('time is ', datetime.time())
        st.color_picker('choose color')


    a1()
################################## when show analysisi click
    if st.sidebar.button("Show Analysis"):


            ###################### main data frame



        # back ground image
        def add_bg_from_url():
            st.markdown(
                f"""
                      <style>
                      .stApp {{
                          background-image: url("https://images.squarespace-cdn.com/content/v1/5cb06a6cd7456246c1156693/1583858428838-08JDDER1VRLWJWYUIX28/IMG_0246.JPG");
                          background-attachment: fixed;
                          background-size: cover
                      }}
                      </style>
                      """,
                unsafe_allow_html=True
            )


        add_bg_from_url()

        new_title = '<p style="font-family:sans-serif; color:blue; font-size: 46px;">welcome to the chat analyzer of WhatsApp</p>'

        st.markdown(new_title, unsafe_allow_html=True)
 ###################################################### main caller
        num_messages, words, num_media_messages, num_links = fatch_stats(selected_user, df)
        new_title = '<p style="font-family:sans-serif; color:red; font-size: 50px;">Top Statistics</p>'
        st.markdown(new_title, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            new_title = '<p style="font-family:sans-serif; color:orange; font-size: 30px;">Total Messages</p>'
            st.markdown(new_title, unsafe_allow_html=True)
            st.title(num_messages)
        with col2:
            new_title = '<p style="font-family:sans-serif; color:white; font-size: 30px;">Total words</p>'
            st.markdown(new_title, unsafe_allow_html=True)
            st.title(words)
        with col3:
            new_title = '<p style="font-family:sans-serif; color:green; font-size: 30px;">Total Media shared</p>'
            st.markdown(new_title, unsafe_allow_html=True)
            st.title(num_media_messages)
        with col4:
            new_title = '<p style="font-family:sans-serif; color:yellow; font-size: 30px;">Total Links </p>'
            st.markdown(new_title, unsafe_allow_html=True)
            st.title(num_links)


        # timeline(monthly)
        st.title("                         ")
        new_title = '<p style="font-family:sans-serif; color:yellow; font-size: 30px;">Monthly Timeline </p>'
        st.markdown(new_title, unsafe_allow_html=True)
        timeline = monthly_timline(selected_user, df)
        fig, ax = plt.subplots()
        ax.plot(timeline['time'], timeline['message'], color='green')
        plt.xticks(rotation='vertical')
        plt.xlabel("Month name")
        plt.ylabel("Number of messages")
        st.pyplot(fig)

        # timeline(daily)
        new_title = '<p style="font-family:sans-serif; color:blue; font-size: 30px;">Daily Timeline </p>'
        st.markdown(new_title, unsafe_allow_html=True)
        daily_timeline = daily_timeline(selected_user, df)
        fig, ax = plt.subplots()
        ax.plot(daily_timeline['only_date'], daily_timeline['message'], color='red')
        plt.xticks(rotation='vertical')
        plt.xlabel("Days")
        plt.ylabel("Number of messages")
        st.pyplot(fig)

        # activity map

        new_title = '<p style="font-family:sans-serif; color:red; font-size: 30px;">Activity map </p>'
        st.markdown(new_title, unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            new_title = '<p style="font-family:sans-serif; color:yellow; font-size: 20px;">Most busy day </p>'
            st.markdown(new_title, unsafe_allow_html=True)
            busy_day = week_activity_map(selected_user, df)
            fig, ax = plt.subplots()
            ax.bar(busy_day.index, busy_day.values)
            plt.xticks(rotation='vertical')
            plt.xlabel("Days")
            plt.ylabel("Number of messages")
            st.pyplot(fig)

            with col2:
                new_title = '<p style="font-family:sans-serif; color:orange; font-size: 20px;">Most busy month </p>'
                st.markdown(new_title, unsafe_allow_html=True)
                busy_month = month_activity_map(selected_user, df)
                fig, ax = plt.subplots()
                ax.bar(busy_month.index, busy_month.values, color='orange')
                plt.xticks(rotation='vertical')
                plt.xlabel("Month")
                plt.ylabel("Number of messages")
                st.pyplot(fig)

            # heatmap
            new_title = '<p style="font-family:sans-serif; color:green; font-size: 30px;">weekly Activity Map </p>'
            st.markdown(new_title, unsafe_allow_html=True)
            user_heatmap = activity_heatmap(selected_user, df)
            fig, cx = plt.subplots()
            t1= sns.heatmap(user_heatmap)
            st.pyplot(fig)

            # finding the busiest user in the group
        if selected_user == 'overall':
            new_title = '<p style="font-family:sans-serif; color:green; font-size: 30px;">Most busy user  </p>'
            st.markdown(new_title, unsafe_allow_html=True)
            x, new_df = most_busy_Users(df)
            fig, bx = plt.subplots()

            col1, col2 = st.columns(2)
            with col1:
                bx.bar(x.index, x.values, color='red')
                plt.xticks(rotation='vertical')
                plt.xlabel("usres")
                plt.ylabel("messages")
                st.pyplot(fig)
            with col2:
                new_title = '<p style="font-family:sans-serif; color:green; font-size:40x;">dataframe  </p>'
                st.markdown(new_title, unsafe_allow_html=True)
                st.dataframe(new_df)

    #MOST COMMON WORDS APP
        most_common_df = most_common_words(selected_user, df)
        fig, ax = plt.subplots()
        ax.barh(most_common_df[0], most_common_df[1])
        plt.xticks(rotation='vertical')
        new_title = '<p style="font-family:sans-serif; color:blue; font-size: 30px;">Most common words  </p>'
        st.markdown(new_title, unsafe_allow_html=True)
        plt.xlabel("Number of word call")
        plt.ylabel("words ")
        st.pyplot(fig)

        # emoji anaalysis
        emoji_df = emoji_helper(selected_user, df)
        new_title = '<p style="font-family:sans-serif; color:red; font-size: 30px;">Emoji analysis  </p>'
        st.markdown(new_title, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(emoji_df)
        with col2:
            new_title = '<p style="font-family:sans-serif; color:red; font-size: 30px;">TOP 5 EMOJI </p>'
            st.markdown(new_title, unsafe_allow_html=True)
            fig, ax = plt.subplots()
            ax.pie(emoji_df[1].head(), labels=emoji_df[0].head(),autopct = "%0.2f")
            st.pyplot(fig)
    a2()
    a3()
st.balloons()