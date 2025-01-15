import google.generativeai as genai
import streamlit as st
import time
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime

genai.configure(api_key="AIzaSyCSCclxMKdQWroYER0f3vkVY4ywzRebAJU")
model = genai.GenerativeModel("gemini-1.5-pro-latest")

# conn = sqlite3.connect("ChatbotDatabase.db")
# cursor = conn.cursor()
# cursor.execute("CREATE TABLE IF NOT EXISTS User(Username TEXT, Password TEXT, UserId INTEGER PRIMARY KEY AUTOINCREMENT)")
# cursor.execute("CREATE TABLE IF NOT EXISTS UserChats(ChatId INTEGER PRIMARY KEY AUTOINCREMENT, ChatName TEXT, CreationDate TEXT, UserId INTEGER, FOREIGN KEY(UserId) REFERENCES User(UserId))")
# cursor.execute("CREATE TABLE IF NOT EXISTS chatbotMessages(messageId INTEGER PRIMARY KEY AUTOINCREMENT, You TEXT, Chatbot TEXT, ChatId INTEGER, FOREIGN KEY(ChatId) REFERENCES UserChats(ChatId))")
# conn.close()

st.session_state["messageHistory"] = []

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

def messagesHistory():
    conn = sqlite3.connect("ChatbotDatabase.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chatbotMessages WHERE ChatId = ?",(st.session_state["Chat"][0],))
    messageHistory = cursor.fetchall()
    conn.close()
    
    history = []
    for message in messageHistory:
        history.append(
        f"Message ID: {message[0]}\n"
        f"Chat ID: {message[3]}\n"
        f"You: {message[1]}\n"
        f"Chatbot: {message[2]}\n")
        
    return history

def chatVerification(userID):
    conn  = sqlite3.connect("ChatbotDatabase.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM UserChats WHERE UserId = ?", (userID,))
    if cursor.fetchone() != None:
        conn.close()
        return True
    else:
        conn.close()
        return False
    
def createChat(name):
    conn  = sqlite3.connect("ChatbotDatabase.db")
    cursor = conn.cursor()
    now = datetime.now()
    cursor.execute("INSERT INTO UserChats(ChatName, UserId, CreationDate) VALUES (?, ?, ?)", (name, st.session_state["UserId"], now.strftime("%d/%m/%Y %H:%M")))
    conn.commit()
    chats = cursor.execute("SELECT * FROM UserChats WHERE UserId = ?", (st.session_state["UserId"],)).fetchall()
    for chat in chats:
        if chat[2] == now.strftime("%d/%m/%Y %H:%M") and chat[1] == name:
            st.session_state["Chat"] = chat
    conn.close()
    st.rerun()
    
if st.session_state["logged_in"] == False:
    st.title("Chatbot")
    col1, col2 = st.columns(2)
    with col1:
        # if st.button("Register"):
        with st.form("registerForm"):
            st.write("Register")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Submit")
            if submit:
                conn = sqlite3.connect("ChatbotDatabase.db")
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM User WHERE Username = ?", (username,))
                user = cursor.fetchone()
                if user == None:
                    conn = sqlite3.connect("ChatbotDatabase.db")
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO User(Username, Password) VALUES (?, ?)", (username, password))
                    conn.commit()
                    conn.close()
                else:
                    st.write("Someone Already has that username")
                    conn.close()

    with col2: 

        with st.form("loginForm"):
            st.write("Login")
            username = st.text_input("Username", key="loginUsername")
            password = st.text_input("Password", type="password", key="loginPassword")
            submit = st.form_submit_button("Submit")
            if submit:
                conn = sqlite3.connect("ChatbotDatabase.db")
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM User WHERE Username = ? AND Password = ?", (username, password))
                user = cursor.fetchone()
                if user != None:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.session_state["UserId"] = user[2]
                    # st.success(f"Welcome, {username}!")
                    if chatVerification(st.session_state["UserId"]) == False:
                        createChat("First Chat")
                    cursor.execute("SELECT * FROM UserChats WHERE UserId = ?", (st.session_state["UserId"],))
                    chat = cursor.fetchone()
                    st.session_state["Chat"] = chat
                    st.rerun()
                    conn.close()
                else:
                    st.write("Login Failed")
               

if st.session_state["logged_in"] == True:
    sidebar = st.sidebar
    sidebar.title("Your Chats")
    conn = sqlite3.connect("ChatbotDatabase.db")
    cursor = conn.cursor()
    with sidebar:
        colNewChat, colLogout = st.columns(2)
        cursor.execute("SELECT * FROM UserChats WHERE UserId = ? ",(st.session_state["UserId"],))
        chats = cursor.fetchall()
        @st.dialog("New Chat")
        def newChatDialog():
            chatName = st.text_input("Chat Name")
            if st.button("Submit"):
                createChat(chatName)
        with colNewChat:
            if st.button("New Chat"):
                newChatDialog()
        with colLogout:
            if st.button("Logout"):
                st.session_state["logged_in"] = False
                st.session_state["username"] = ""
                st.session_state["UserId"] = 0
                st.session_state["Chat"] = ""
                st.rerun()
                
        for chat in chats:
            colName, colDelete = st.columns(2)
            with colName:
                if st.button(chat[1], type="tertiary"):
                    st.session_state["Chat"] = chat
            with colDelete:
                if(len(chats)>1):
                    if st.button("Delete", type="primary", key=chat[0]):
                        cursor.execute("DELETE FROM UserChats WHERE ChatId = ?", (chat[0],))
                        conn.commit()
                        cursor.execute("SELECT * FROM UserChats WHERE UserId = ?", (st.session_state["UserId"],))
                        chat = cursor.fetchone()
                        st.session_state["Chat"] = chat
                        st.rerun()
                    
    cursor.execute("SELECT * FROM chatbotMessages WHERE ChatId = ?",(st.session_state["Chat"][0],))
    messageList = cursor.fetchall()
    conn.close()

    def stream_data(response):
        for word in response.split(" "):
            yield word + " "
            time.sleep(0.02)
    st.title(st.session_state["Chat"][1], )
    
    for message in messageList:
            if message != None:
                with st.chat_message("You"):
                        st.write("You")
                        st.write(message[1])
                with st.chat_message("Chatbot"):
                        st.write("Chatbot")
                        st.write(message[2])

    prompt = st.chat_input("Say something")
    messages = messagesHistory()
    context = ("\n".join(messages))
    promptWithHistory = f"{context}\nYou: {prompt}\nChatbot:"
    if prompt:
        with st.chat_message("You"):
            st.write("You")
            st.write(prompt)
        with st.chat_message("Chatbot"):
            st.write("Chatbot")
            response = model.generate_content(promptWithHistory)
            st.write_stream(stream_data(response.text))
        conn = sqlite3.connect("ChatbotDatabase.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO chatbotMessages(You, Chatbot, ChatId) VALUES (?, ?, ?)", (prompt, response.text, st.session_state["Chat"][0]))
        conn.commit()
        conn.close()
        


    