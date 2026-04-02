#Build with AI: AI-Powered Dashboards with Streamlit 
#Use AI to Explore and Summarize Your Data

#Import packages
import streamlit as st
import pandas as pd
import runpy, tempfile, os, pickle
from openai import OpenAI
from dotenv import load_dotenv



#Open file with API key
load_dotenv(override=True)
my_api_key = os.getenv("OPENAI_API_KEY")

#Initialize OpenAI client with your API key
client = OpenAI(api_key=my_api_key)


#Write title
st.title("DATA EXPLORATION WITH AI")

#Load revenue and expenses file
df_rev_exp = pd.read_excel("Landon_Hotel_Revenue_And_Expenses.xlsx")
#Load location file
df_loc = pd.read_excel("Landon_Hotel_Location.xlsx")
#Merge datasets on 'Hotel ID'
df = df_rev_exp.merge(df_loc, on="Hotel ID", how="outer")

#Add subheader for merged data preview
st.subheader("Merged Data Preview")
#Display first few rows of merged data
st.dataframe(df.head())

#Determine if chat history exists in the session state and initialize if it doesn't
if "history" not in st.session_state:
    st.session_state.history = []

#Create text input field on main page to allow users to type in question
query = st.text_input(
    "Ask the AI to explore or summarize your DataFrame (e.g. 'show me summary statistics for expenses')"
)

#Check if 'Ask AI' button is clicked
if st.button("Ask AI"):
    #Provide warning if user has not entered a question
    if not query.strip():
        #Add user's message to chat history
        st.warning("Enter a question before sending.")
    else:
        #Display a spinner while querying AI
        with st.spinner("Quering AI ..."):
            try:    
                #Send chat history and instructions to OpenAI LLM and receive response
                resp = client.chat.completions.create(
                    #Select model
                    model="gpt-3.5-turbo",
                        #Define assistant's role and instructions
                    messages=[
                        {"role": "system", "content": (
                            "You are a data analyst. Given a pandas DataFrame df, "
                            "respond with a python code block to perform the requested analysis on df. "
                            "Always assign the final result to a variable called result, so it can be retrieved after execution."
                        )},
                        #Send user's query
                        {"role": "user", "content": query}
                    ]
                )
                        
                #Define function to clean AI's code response by removing markdown markers
                def clean_code_response(raw_code):
                    code = raw_code.strip()
                    #Remove ``` markdown markers if present
                    if code.startswith("```"):
                        parts = code.split("```")
                        code = "".join(parts[1:])
                    #Remove any standalone 'python' lines
                    code_lines = code.splitlines()
                    code_lines = [line for line in code_lines if line.strip().lower() != "python"]
                    return "\n".join(code_lines).strip()
                
                #Gather assistant's raw reply
                raw_response = resp.choices[0].message.content
                #Clean AI response to extract Python code only
                clean_code = clean_code_response(raw_response)


                #Add subheader for AI response
                st.subheader("AI-Generated Code")

                #Display extracted AI-generated code with syntax highlighting
                st.code(clean_code, language="python")

                #Save current dataframe to a pickle file for use by temp code
                with open("df.pkl", "wb") as f:
                    pickle.dump(df, f)

                #Create temporary Python script containing AI-generated code
                temp_code = f"""
import pickle

# load the dataframe from the pickle file
with open("df.pkl", "rb") as f:
    df = pickle.load(f)


# AI generated code starts here
{clean_code}

# save results
try:
    result
except NameError:
    try:
        result = expenses_summary
    except:
        try:
            result = payroll_summary
        except:
            result = "No result variable found in AI code."

with open("result.pkl", "wb") as f:
    pickle.dump(result, f)
"""


                #Create a temporary file to write the AI Python code into
                with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp:
                    tmp.write(temp_code)
                    tmp.flush()
                    temp_file_path = tmp.name
                
                #Run temporary Python file after it's closed and written to disk
                runpy.run_path(temp_file_path)
                
                #Delete temporary file after running
                os.remove(temp_file_path)

                #Load result back from the pickle file
                with open("result.pkl", "rb") as f:
                    result = pickle.load(f)

                #Add subheader for execution result
                st.subheader("Execution Result")
                #Display the result when the code is run
                st.write(result)

                #Add assistant's reply to chat history
                st.session_state.history.append(("Bot", clean_code))
                st.session_state.history.append(("Bot", result))

            #Handle API and execution errors and add to chat history
            except Exception as e:
                error_message = f"Error: {str(e)}"
                st.error(error_message)
                st.session_state.history.append(("Bot", error_message))

#Add chat window to display messages
st.subheader("Summary History")
#Loop through the chat history stored in session state and display each message
for role, msg in st.session_state.history:
    #Check if message is from user and display it
    if role == "User":
        st.write(f"**User:** {msg}")
    #Otherwise display assistant's response as info box
    else:
        st.info(f"**Bot:** {msg}")
