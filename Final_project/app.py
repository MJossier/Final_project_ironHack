from flask import Flask, render_template, request, jsonify
from googletrans import Translator # Importing Translator from googletrans package for translation
from langdetect import detect # Importing detect function from langdetect for language detection
# launchion the flas app name 
app = Flask(__name__) # Creating a Flask app instance
# Define predefined script questions that Bot will ask
script = {
    "questions": [
        "Do you have the user screenshot? \n\nIf yes, input the user screenshot; \n\nOtherwise, reply N/A.",
        "Can you provide me the user message? Please input it.",
        "Are there any debug logs from the user? \n Please input your answer yes or no.",
        "Are there any duplicates from the user? \n Please input your answer yes or no.",
        "Are there any actions taken at the account level? Please input your answer yes or no\n\n Please add ok to get your notes."
    ],
    "resolution": [
        "Please find below your notes that you can copy-paste: \n\n{user_notes}\n\n Please add ok to get the email of the user."
    ],
    "reply": [
        "Please find below the reply for your user:\n\n",
        # Template for reply
        "{docword}"
    ]
}

# Variable to keep track of the current step in the conversation
current_step = 0

# Define user notes template

user_notes_template = """
Add a screenshot of the Wazetool user\n{user_screenshot}

What is the type of issue escalated by the user according to your analysis? \n
{user_message}

Are there any logs in debug? \n{debug_logs}

Are there any duplicates? \n{duplicates}

Are there any actions taken at the account level? 
{account_actions}
"""

# Dictionary to store user responses global variable 
user_responses = {}
user_notes = ""
# email template
docword_no_account = """\n\nHi there Wazer,\n

Thank you for contacting Waze about your login issue, we are here to help.\n
Unfortunately, we currently don't offer French support on our help channels, but we'd be happy to assist you in English.\n

You can follow the steps below to get access to your account with your email.\n
Make sure:\n
There aren’t any typos in your email address\n
You’ve entered your full email address – for example, “username@gmail.com” instead of “username@gmail”\n
Caps lock is turned off\n
Your keyboard is in the right language\n
Note: If your email inbox is on another device than the one you're using to sign in, do the following:\n
Open your inbox from a web browser
Open the verification email and tap Verify email. A new tab will open with a verification code.
In Waze, enter the code \n
Still having issues?
Try another email that isn’t your main account.\n
If you added a username and password to your account, try entering them instead
Make sure there are no typos
If you forgot your password, learn how to reset it
\n
Consider creating a new Waze account:
Open the Waze app on your phone or tablet
Tap Get started
Sign up to Waze – we recommend creating your own account by choosing one of the available signup options instead of Continue as Guest
Having trouble creating an account? Get help.
\n
You can find more information about Waze in our help center.
If all the steps before don't work, please reply to this email in English with a more detailed description of your issue, so we can better assist you.
\n
Best,
Mickael
Waze Support Team
"""

docword_email_not_verified = """\n\n
Hi There Wazer,\n
Thank you for contacting us about your verification email issue.\n


Unfortunately, we currently don't offer French support on our help channels, but we'd be happy to assist you in English.\n
If you didn’t get a verification email, try the following:\n
Make sure there aren’t any typos in your email address
Make sure you’ve entered your full email address – for example, “username@gmail.com” instead of “username@gmail”
Make sure you’re in the inbox of the correct email address
Check your email’s spam folder for the verification code
Search for “noreply@waze.com”
Note: If your email inbox is on another device than the one you're using to sign in, do the following:
Open your inbox from a web browser
Open the verification email and tap Verify email. A new tab will open with a verification code.
In Waze, enter the code \n
Still need help?\n
Let's try again:
Open Waze on your mobile device
Tap Sign in
Enter your email address
Tap Next
Using email on your mobile device?
Go to your inbox
Open the verification email
Tap Verify email
Note: You will be taken back to the Waze app automatically.\n

Using email on a web browser?
Go to your inbox
Open the verification email
Click Verify email. A new browser will open with the code.
Enter the code in Waze\n\n
You can find more information about email verification with Waze in our help center.
\n
If you still have questions, feel free to reply and I’d be happy to help. \n
If possible, please reply in English so we can continue to handle the case.\n
Best,\n
Mickael 
Waze Support Team\n

"""

docword3_log_in_facebook = """\n\n
Hi there Wazer,\n
Thanks for contacting us about your login issue. We’re here to help. \n
Unfortunately, we currently don't offer French support on our help channels, but we'd be happy to assist you in English.\n
As of June 2020, you can no longer sign in to Waze with your phone number or with your Facebook account. To prepare for this, we asked that users add an email account to Waze and verify it before June.
If you didn’t do this, you will need to create a new Waze account:\n
Go back to the screen with the Get started button
Tap Get started
I still can’t sign in to Waze
Consider creating a new Waze account:
Open the Waze app on your phone or tablet
Tap Get started
Sign up to Waze –\n we recommend creating your own account by choosing one of the available signup options instead of Continue as Guest
Having trouble creating an account? Get help.
\nYou can find more information about login Waze in our help center.
\nIf all the steps before don't work, please reply to this email in English with a more detailed description of your issue, so we can better assist you.
 
Best,
Mickael 
Waze Support Team

"""


# detect if it's French
def detect_language(user_message):
    global language_code
    try:
        language_code = detect(user_message)
        return language_code
    except Exception as e:
        print(f"Error detecting language: {e}")
        return "en"  # Return default language (English)
    
def traduction_message(user_message):
     if language_code == 'fr': # if language is french detect it and translate
                translator = Translator()
                translated_message = translator.translate(user_message, dest='en').text
                print(translated_message)
            # Add a sentence indicating that the message has been translated
                user_responses["user_message"] = translated_message  
                user_responses["user_message"] += "\n\nUser message is French."

# this select the template base on key work

def templateselection(user_message):
    if "no account found" in user_message:
        selected_template = docword_no_account
    elif "email" in user_message:
        selected_template = docword_email_not_verified
    elif "facebook" in user_message or "phone" in user_message:  # Adjusted condition
        selected_template = docword3_log_in_facebook
    else:
        selected_template = docword_no_account  # Default template
    return selected_template



# translate message in english

# Function to handle user input and provide responses
def get_chatbot_response(user_input):
    global current_step # set variable as global so they can be used in any function
    global user_responses 
    global user_notes
    global user_message
    

    if current_step <= len(script["questions"]):
        # Store the user's response with keys corresponding to the placeholders in user_notes_template
        if current_step == 1:
            user_responses["user_screenshot"] = user_input # store user message with corresponding question
        elif current_step == 2:
            user_responses["user_message"] = user_input
            user_message = user_input
        elif current_step == 3:
            user_responses["debug_logs"] = user_input
        elif current_step == 4:
            user_responses["duplicates"] = user_input
        elif current_step == 5:
            user_responses["account_actions"] = user_input

        current_step += 1
        # Move to the next question
        return script["questions"][current_step - 1] # ask the next question // one step before the answer
    
    elif current_step == len(script["questions"]) + 1:
        current_step += 1
    
        # Store the current user's message before generating user_notes
        user_notes = user_notes_template.format(**user_responses)
        # Return the resolution template with user notes
        return script["resolution"][0].format(user_notes=user_notes)
    elif current_step == len(script["questions"]) + 2:
        current_step += 1
        # Return the predefined email template
        return templateselection(user_message)
        # Return the reply template
        
    else:
        # Return the resolution template with user notes
        return 'Please reload the page for a new case'


# this function refreshe the page and proceed to some change before lauching the scrip as definiyng global

@app.before_request
def before_request():
    global current_step
    global user_responses
    if request.path == '/':
        current_step = 0
        user_responses = {}

# Home route to render index.html
        # show the website page front end html and Java code
@app.route('/')
def index():
    return render_template('index.html')

#

# Route to process user message
@app.route('/process_user_message', methods=['POST'])
def process_user_message():
    global current_step
# to check if bacl ennd receive the mesage well
    if not request.json or 'user_message' not in request.json:
        return jsonify({'error': 'Invalid request format'}), 400

    user_input = request.json.get('user_message')

    # Check if user input is empty
    if not user_input.strip():
        if current_step == 0:
            return jsonify({'response': 'You did not enter a message. Please try again.'}), 200
        else:
            # If user did not enter a message, repeat the previous question
            current_step -= 1
            return jsonify({'response': script["questions"][current_step]}), 200

    # Get response from predefined script
    response = get_chatbot_response(user_input)

    return jsonify({'response': response})



# Main function to run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
