
import matplotlib
matplotlib.use('Agg')
from flask import Flask, render_template, request, jsonify
import flask_cors
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import re
import pytesseract
from PIL import Image
from fuzzywuzzy import process
import matplotlib.pyplot as plt
import base64
import io

pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'  # Required for Render/Linux
app = Flask(__name__)
CORS(app)
# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure Tesseract executable path
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Comprehensive reference ranges for a wide variety of tests
medical_tests = {
    # Complete Blood Count (CBC)
    "Hemoglobin": (11.6, 16.6),       # g/dL
    "RBC Count": (3.9, 6.1),            # million cells/mcL
    "WBC Count": (4000, 11000),         # cells/mcL
    "Platelet Count": (150, 450), # platelets/mcL
    "PCV": (40, 50),                  # percentage
    "MCV": (80, 100),                 # fL
    "MCH": (27, 32),                  # pg/cell
    "MCHC": (32, 36),                 # g/dL
    "RDW": (11.5, 14.5),              # %
    "Neutrophils": (1.5, 7.0),          # x10^9/L
    "Lymphocytes": (1.0, 4.8),          # x10^9/L
    "Monocytes": (0.2, 1.0),            # x10^9/L
    "Eosinophils": (0.0, 0.5),          # x10^9/L
    "Basophils": (0.0, 0.2),            # x10^9/L,
    
    # Basic Metabolic Panel (BMP)
    "Glucose": (70, 100),               # mg/dL (fasting)
    "Calcium": (8.5, 10.5),             # mg/dL
    "Sodium": (135, 145),               # mEq/L
    "Potassium": (3.5, 5.0),            # mEq/L
    "Chloride": (95, 105),              # mEq/L
    "Bicarbonate": (22, 29),            # mEq/L
    "BUN": (10, 20),                    # mg/dL
    "Creatinine": (0.6, 1.2),           # mg/dL

    # Comprehensive Metabolic Panel (CMP) additional tests
    "Total Protein": (6.0, 8.3),        # g/dL
    "Albumin": (3.4, 5.4),              # g/dL
    "Globulin": (2.0, 3.5),             # g/dL
    "ALP": (30, 120),                   # U/L
    "ALT": (7, 55),                     # U/L
    "AST": (8, 48),                     # U/L
    "Bilirubin": (0.2, 1.2),              # mg/dL

    # Lipid Panel
    "Total Cholesterol": (0, 200),      # mg/dL
    "LDL Cholesterol": (0, 100),        # mg/dL
    "HDL Cholesterol": (40, float('inf')),  # mg/dL, using float('inf') to denote no upper limit
    "Triglycerides": (0, 150),          # mg/dL

    # Thyroid Function Tests
    "TSH": (0.4, 4.0),                  # mIU/L
    "Free T4": (0.8, 1.8),              # ng/dL

    # Coagulation Tests
    "PT": (11, 13),                     # seconds
    "INR": (0.8, 1.2),                  # unitless (unless on anticoagulants)
    "aPTT": (25, 35),                   # seconds
    "HbA1c": (0, 5.7),                  # % for non-diabetics

    # Cardiac Enzymes
    "Troponin": (0, 0.04),              # ng/mL
    "CK": (55, 170),                    # U/L (for men, adjust as needed for women)

    # Inflammatory Markers
    "CRP": (0, 10),                     # mg/L
    "ESR": (0, 15),                     # mm/hr for men (adjust for women if needed)
    
    # You can extend this dictionary as necessary for other tests...
}

# Explanation and recommendation databases
# Updated explanations dictionary: additional text for tests when levels are LOW or HIGH
explanations = {
    "low": {
        "Hemoglobin": "Oh no, your hemoglobin has gone on a vacation! 🩸 Feeling weak, dizzy, or out of breath? Maybe it's just tired of carrying oxygen all day! Or did a secret vampire snack on your blood? Time to check if your body’s sending out distress signals!",
        "RBC Count": "Your red blood cells are running on low power! 🔋 They carry oxygen, so if they’re slacking, you might feel tired, pale, or out of breath. Did your body forget to manufacture them, or did some escape without telling you?",
        "WBC Count": "Your immune army is understaffed! 🛡️ Hope no germs are planning a sneak attack! If you’ve been falling sick easily, your body’s defenses might need some reinforcement!",
        "Platelet Count": "Uh-oh! Your platelet squad is snoozing! 🩸 Watch out for random bruises—maybe they forgot their job of clotting!",
        "PCV": "Your blood is feeling a bit thin, huh? Low PCV might mean you're a bit over-hydrated or perhaps your body's having an anemia moment. Let's find out what's really going on! 💧",
        "MCV": "Your red blood cells are looking a little skinny! 🤏 Low MCV often points to microcytic anemia, like when your body's crying out for more iron. Time to feed those tiny cells! 🍎",
        "MCH": "Looks like your red blood cells are running on low color! 🎨 Low MCH frequently happens with iron deficiency anemia. Let's add some pigment back into those hardworking cells! ✨",
        "MCHC": "When your red blood cells look 'pale,' low MCHC is often the tell-tale sign of hypochromic anemia. It's like they're just not getting enough color! Let's brighten them up! 🌟",
        "RDW": "Your red blood cells are showing off their diversity, but maybe a bit too much! 🧐 An abnormal RDW could mean your anemia is a complex story with many different players. Time for a full investigation! 🕵️‍♀️",
        "Neutrophils": "Your first line of defense, the neutrophils, are taking a nap! 😴 This might signal a viral party crashing your system or perhaps your bone marrow is feeling shy. Time to wake them up!",
        "Lymphocytes": "Feeling a bit exposed? Your lymphocyte counts are on the low side! 📉 This could hint at some immune system vulnerabilities. Let’s make sure your body’s special forces are ready for action! 🛡️",
        "Monocytes": "Your monocytes are playing it cool and staying low! 😎 Usually, this isn't a huge drama. But if you’re feeling under the weather, it's always worth a peek, just in case! 😉",
        "Eosinophils": "Low eosinophils? That's typically a 'nothing to see here' moment! 🤷‍♀️ Your body's just keeping things chill and balanced. Don't sweat it!",
        "Basophils": "A very low basophil count? You're basically a chill celebrity – generally not problematic at all! 🌟 Keep living your best life!",
        "Glucose": "Your blood sugar is on a downward spiral! 🍬 If you’re feeling weak, shaky, or craving sweets like a dessert monster, something might be up!",
        "Calcium": "Your bones and nerves are missing their favorite nutrient! 🦴 Muscle cramps or tingling could mean your calcium’s too low—your skeleton deserves better!",
        "Sodium": "Whoa, your sodium's gone on a salty escape! 🧂 Feeling confused or having strange zaps? Low sodium (hyponatremia) can really shake things up. Let's get that balance back! ⚖️",
        "Potassium": "Your muscles might be staging a rebellion! 💪 Low potassium could mean leg cramps, weakness, or even an irregular heartbeat—let’s keep an eye on this!",
        "Chloride": "Your chloride is a bit low, and it usually means it brought friends! 👯‍♀️ It often tags along with other electrolyte imbalances. Time to check the whole crew! 🕵️‍♂️",
        "Bicarbonate": "A dip in your bicarbonate could mean your body's acidity is going up! 🍋 It's like your internal pH balance is a little out of whack, pointing to metabolic acidosis. Let's fix that! 🧪",
        "BUN": "Your BUN (blood urea nitrogen) is being a bit of a low-key player! 🤫 This might signal you’re super hydrated or maybe not getting enough protein in your diet. Time for a quick check-in! 💧🥩",
        "Creatinine": "Low creatinine? Relax, it's usually just minding its own business and not a big worry on its own! 🧘‍♀️ Your kidneys are probably just chilling. Good job, kidneys!",
        "Total Protein": "Feeling a bit drained? Your total protein could be whispering 'malnutrition' or hinting that your liver needs a little extra love. Time to fuel up those building blocks! 🏗️",
        "Albumin": "Your body's main transport protein, albumin, is taking a dive! 📉 This might signal your liver or kidneys are throwing a little tantrum. Time to investigate what's got them down! 🕵️‍♀️",
        "Globulin": "Low globulin? This superhero protein helps your immune system! 🦸‍♀️ A dip might mean your body's defenses aren't quite at superhero strength. Let's power them up!",
        "ALP": "Low alkaline phosphatase? This is a bit of a rare bird and usually not a big concern! 🐦 It *could* hint at some nutritional needs, but don't panic! 😉",
        "ALT": "Good news, your ALT is taking a low profile! 🎉 Low levels are generally way less concerning than high ones. Your liver's probably just enjoying a quiet day! 😌",
        "AST": "Your AST is chilling out and staying low! 😴 This usually means no problem at all. Nothing to see here, folks, move along! 👋",
        "Bilirubin": "Low bilirubin? That's typically a 'no worries, mate!' sign! ✅ Your body's clearing things out perfectly fine. Keep up the good work!",
        "Total Cholesterol": "Your total cholesterol is looking a bit shy! 🧐 This could hint at some malnutrition. Time to ensure you're getting enough of the good stuff to keep everything balanced! 🥑",
        "LDL Cholesterol": "Low LDL cholesterol? You hit the jackpot! 🎰 That's usually a high-five moment for your heart. Keep up the fantastic work! 💖",
        "HDL Cholesterol": "Oops, your 'good' HDL cholesterol is playing it low! 📉 This means your heart might need a little extra TLC to keep those cardiovascular risks at bay. Time to give it some love! ❤️‍🩹",
        "Triglycerides": "Low triglycerides? Excellent! 🎉 Generally, nothing to be concerned about here. You're doing great, keep shining!",
        "TSH": "Your thyroid stimulating hormone (TSH) is taking a dip! 🏊‍♀️ This might be your thyroid working overtime, hinting at hyperthyroidism. Time for a chat with your thyroid's boss! 🗣️",
        "Free T4": "Feeling a bit sluggish? Your free T4 is on the low side! 😴 This could mean your thyroid is taking a long nap, hinting at hypothyroidism. Time to wake it up and get it buzzing! 🐝",
        "PT": "A quick PT time? Generally, that's not something to fret about! 👍 Your blood is doing its clotting job efficiently. High five for good clotting!",
        "INR": "Your blood is clotting a bit too quickly, judging by that low INR! 🏎️ If you're on blood thinners, this might need a quick pit stop to adjust things. Stay in the safe lane!",
        "aPTT": "A short aPTT could mean your blood is super eager to clot! ⚡ This might indicate a hypercoagulable state, so it's definitely worth a peek with a doctor. Don't let it get *too* enthusiastic!",
        "HbA1c": "Super low HbA1c? Could be excellent blood sugar control, or perhaps the measurement is a little off. 🤔 Let's double-check to find your body's sweet spot! 🎯",
        "Troponin": "Low troponin? Perfect, that's exactly what we want to see! ❤️ Your heart is happy, chilling like a villain! Keep it up!",
        "CK": "Low CK? Don't stress, it's usually not concerning at all! 😌 Your muscles are just playing it cool and not breaking a sweat. Literally!",
        "CRP": "Low CRP? Fantastic! 🎉 This is a clear sign your inflammation levels are nice and chill. Keep up those healthy habits, you superstar! ✨",
        "ESR": "A low ESR? That's usually a good report card for your body, suggesting low inflammation! 🥳 Your body is calm, cool, and collected!"
    },
    "high": {
        "Hemoglobin": "Whoa, your hemoglobin is on overdrive! 🏃‍♂️ Have you been training for a marathon without knowing? Dehydration or polycythemia might be behind this high score!",
        "RBC Count": "Your red blood cells are working overtime, like tiny overachievers! 📈 A high RBC count could indicate polycythemia or simply that you need to drink more water. Hydration station, please! 💦",
        "WBC Count": "Your immune forces are charging forward! 🔥 Fighting an infection or just flexing too hard? If your body’s acting like it’s in battle mode, something might be going on!",
        "Platelet Count": "Your platelets are having a party! ⚡ Clots might form too fast, so keep an eye on any unusual symptoms. They might be getting a little *too* enthusiastic!",
        "PCV": "Your PCV is hitting the high notes! 🎶 This often means you're a bit dehydrated, or your body's producing a few too many red blood cells. Time to rehydrate and check it out! 💧",
        "MCV": "Your red blood cells are looking a bit plump! 🎈 High MCV can suggest macrocytic anemia, often from a vitamin B12 or folate deficiency. Time to feed those cells the right nutrients! 🥕",
        "MCH": "Your red blood cells are packed to the brim with hemoglobin! 🎒 High MCH might pop up in macrocytic anemias. Let's figure out what's making them so full! 🤔",
        "MCHC": "High MCHC is a bit of a rare and curious case, like a unicorn! 🦄 It might be due to inherited conditions like spherocytosis. Time for a deeper dive with your doc! 🔬",
        "RDW": "Your red blood cells are a real mixed crowd in terms of size! 🥳 A high RDW means there's a lot of variety, often linked to anemia. What's causing the diversity in your blood cell population? 🕵️‍♂️",
        "Neutrophils": "Your first responders, the neutrophils, are swarming! 🚨 Elevated levels often scream 'bacterial infection' or serious inflammation. Time to find the culprit and kick it out! 🦠",
        "Lymphocytes": "Your lymphocytes are on the rise! 🚀 This could be a viral battle or a long-term chronic condition setting in. Let's figure out what's making them so active! 🕵️‍♀️",
        "Monocytes": "Your monocytes are buzzing and looking quite high! 🐝 This might indicate chronic inflammatory or infectious conditions. Time to investigate what's stirring them up! 🔍",
        "Eosinophils": "High eosinophils? Are you battling allergies or hosting some unwelcome parasitic guests? 🤧🐛 Time for an eviction notice or an allergy check! ",
        "Basophils": "Your basophils are getting a bit too excited! 🥳 Elevated levels can be associated with chronic inflammation or allergic reactions. What's making them so hyper? 🤔",
        "Glucose": "Sugar levels soaring! 🚨 Your blood might be turning into syrup—hope you're not turning into a human candy factory! Keep an eye on this before things get sticky!",
        "Calcium": "Your calcium is acting like it owns the place! 🏗️ Too much of it might mean an underlying condition—your bones love it, but moderation is key!",
        "Sodium": "Your sodium is going through the roof! 🏠 High sodium (hypernatremia) often screams 'dehydration'! Time to chug some water, stat, before things get too salty! 🧂",
        "Potassium": "Warning: your potassium is sky-high! ⚡ If your heart starts doing funky rhythms, that’s your cue to check what’s up!",
        "Chloride": "Your chloride levels are a bit too high! ⬆️ This can sometimes tag along with dehydration or your kidneys acting a little quirky. Time to check the whole electrolyte team! 🤝",
        "Bicarbonate": "Your bicarbonate is elevated! 📈 This might be related to metabolic alkalosis, meaning your body’s pH balance is a bit off. Let's get things back to neutral! ⚖️",
        "BUN": "Your BUN is up in the clouds! ☁️ This is often a shout-out from your kidneys saying they're not quite happy campers. Time for a kidney check-up! 🩺",
        "Creatinine": "High creatinine is a big red flag for your kidneys! 🚩 It suggests they’re not filtering as well as they should. Get this checked ASAP – your kidneys are important! 🚨",
        "Total Protein": "Your total protein levels are looking plump! 🏋️ This could signal chronic inflammation or an ongoing infection. Time to find out what's causing this protein party! 🎉",
        "Albumin": "Your albumin is riding high! 🚀 This usually means you're just a bit dehydrated. Time to grab that water bottle and hydrate, hydrate, hydrate! 💧",
        "Globulin": "Your globulin levels are soaring! 🦅 This often points to chronic infections or inflammatory states. Time to investigate what's got your immune system so busy! 🕵️‍♀️",
        "ALP": "Your ALP (alkaline phosphatase) is doing a happy dance! 💃 An elevated ALP can indicate issues with your liver or bones. Time for a diagnostic jig! 🕺",
        "ALT": "Uh oh, your ALT is elevated! 📈 This is often a clear marker for liver inflammation or injury. Your liver needs some serious TLC and a good check-up! 🤕",
        "AST": "Your AST is looking a bit high! 📈 This might mean some liver or muscle damage has occurred. Time to give those organs a gentle once-over! 🕵️",
        "Bilirubin": "High bilirubin? This is a serious concern for liver disease or if your red blood cells are breaking down too fast! 🚨 Get this checked urgently – your liver is vital! ⚠️",
        "Total Cholesterol": "Your total cholesterol is hitting the high notes! 🎶 This increases your cardiovascular risk. Time for a heart-healthy concert, focusing on diet and exercise! ❤️",
        "LDL Cholesterol": "Your 'bad' LDL cholesterol is elevated! 📈 This is strongly associated with clogged arteries (atherosclerosis). Time to get that number down for a healthier heart! 📉",
        "HDL Cholesterol": "Your 'good' HDL is super high! 🎉 While generally protective, extremely high values are rare and warrant a quick glance from your doctor. Still, mostly a win! 🏆",
        "Triglycerides": "High triglycerides are knocking at your heart's door, increasing risk! 🚪 Time for some serious lifestyle changes to bring them down. Your heart will thank you! ❤️‍🩹",
        "TSH": "Your TSH is high! 📈 This often whispers 'hypothyroidism,' meaning your thyroid is a bit underactive and needs a kickstart. Time to wake it up! 😴",
        "Free T4": "Your free T4 is on a rampage! 🌪️ Elevated levels might mean hyperthyroidism, where your thyroid is working overtime. Time to rein it in! 🐎",
        "PT": "A prolonged PT means your blood is taking its sweet time to clot! ⏳ This could increase your bleeding risk, so be extra careful with sharp objects! 🔪",
        "INR": "Your INR is super high! ⬆️ This means your blood is taking a long, long, LONG time to clot. If you're on thinners, your dose might be too high! This needs immediate attention! 🚨",
        "aPTT": "A prolonged aPTT could indicate some quirky coagulation abnormalities! 🧐 Time to investigate why your blood is being so slow to clot. No need for a race, but don't be a snail! 🐌",
        "HbA1c": "Your HbA1c is high! 📈 This reflects poor long-term blood sugar control. It's like your blood sugar's report card needs a major improvement! Time for some serious studying! 📚",
        "Troponin": "DANGER! Elevated troponin is a critical sign of heart muscle injury! 🚨 Get to the doctor IMMEDIATELY! This is an emergency you can't ignore! ❤️‍🩹",
        "CK": "Your CK is high! ⬆️ This often means some muscle damage has occurred. What have you been lifting? 😉 Or perhaps something more serious needs a check. 💪",
        "CRP": "Your CRP is elevated! 📈 This is a clear sign of systemic inflammation somewhere in your body. It's like your body's fire alarm is blaring! 🔥 Time to find the fire! ",
        "ESR": "Your ESR is high! 📈 This is a non-specific alarm for inflammation. It's like your body's general alert system is going off! 🔔 Time for a closer look!"
    },
}

# Updated recommendations dictionary: guidance based on abnormal values
recommendations = {
    "low": {
        "Hemoglobin": "Time to feast on iron-rich goodies! 🥩🥬 And check if you’ve lost blood somewhere—mystery bleeding isn’t fun! Talk to your doc if you're still feeling like a deflated balloon! 🎈",
        "RBC Count": "Low RBCs? We need to play detective! 🕵️‍♀️ Further tests are key to finding the cause of these oxygen-carrying slackers. And remember, good nutrition is your best friend here! 🥕",
        "WBC Count": "Boost your immune system with good sleep, healthy food, and maybe some detective work to see if an infection is lurking! 🕵️‍♂️ Give your body's defense team a pep talk! 📣",
        "Platelet Count": "Keep an eye on bleeding risks! 🩸 If your platelets stay low, consult a hematologist and maybe stay away from sharp objects (and extreme sports!) for a bit! 🚫",
        "PCV": "If your PCV is low, first, drink up! 💧 Hydration is key. And make sure you're getting enough dietary iron. If symptoms linger, definitely follow up with your doctor – no dilly-dallying! 🩺",
        "MCV": "Your red blood cells are looking a little small! 🤏 Load up on iron-rich foods (spinach, red meat!) and perhaps some supplements. Let's plump up those tiny cells! 🍎",
        "MCH": "To pep up that MCH, focus on iron-rich food intake and possibly some vitamin supplementation. Let's add some vibrant color back into those hard-working red cells! ✨",
        "MCHC": "Got low MCHC? Time to chat with your doctor to unravel the mystery and consider some nutritional interventions. Let's get those cells looking healthy and vibrant again! 😊",
        "RDW": "Your red blood cells are a bit of a motley crew! 🧐 A high RDW means further investigation is needed to understand the variability. What's causing all the diversity in your blood stream? Let's find out! 🔬",
        "Neutrophils": "If those neutrophils are low, it's worth getting more tests to rule out infections or bone marrow quirks. Your body's defense team needs to be strong and ready! 🦸‍♂️",
        "Lymphocytes": "If low lymphocytes are persistent, it's time for some extra evaluations! 🧐 Let's ensure your immune system's special forces are ready for anything. Stay strong! 💪",
        "Monocytes": "Low monocytes usually aren't a big deal, but if you're still feeling under the weather, a quick chat with your healthcare provider is a good idea. Better safe than sorry when it comes to your health! 😉",
        "Eosinophils": "Low eosinophils? Seriously, don't lose sleep over it! 😴 It's usually nothing to worry about. Your body's just keeping it cool! Phew! 😌",
        "Basophils": "Super low basophils? Relax, it's generally not an issue at all! 🎉 But if you suddenly sprout new or concerning symptoms, then it's time to check in with your doctor. Otherwise, keep shining! 🌟",
        "Glucose": "Grab a snack! 🍎 Low sugar might make you dizzy—balance it well and talk to a doctor if it keeps happening!",
        "Calcium": "Milk, cheese, leafy greens—your bones need reinforcement! 🦴 Get your daily dose or consult if symptoms pop up—your skeleton deserves the best!",
        "Sodium": "Low sodium? Hydration is key, but also keep an eye on your salt intake. 🧂 If symptoms appear (like confusion!), don't hesitate to call your physician! 📞",
        "Potassium": "Go bananas (literally)! 🍌 Low potassium? Boost it with potassium-rich foods or supplements! If those muscle cramps persist, re-evaluate with your doc! 💪",
        "Chloride": "If your chloride is low, it means your hydration status and overall electrolyte balance need a little love and fine-tuning. Time for a quick check and some hydration! ⚖️💧",
        "Bicarbonate": "If your bicarbonate is playing low and an acid-base imbalance is suspected, it's time for more tests! 🧪 We need to get your body's internal pH perfectly balanced. Let's get scientific! 🔬",
        "BUN": "Low BUN? Think nutrition and hydration! 🍎💧 Are you eating enough protein and drinking enough water? A quick check-in with your diet and habits might reveal the answer! ",
        "Creatinine": "Low creatinine? Retest and consider your dietary and nutritional factors. Typically, it's a chill number and much less concerning than when it's high! 🧘‍♀️ No need to stress! ",
        "Total Protein": "To boost that total protein, focus on increasing your dietary protein intake! 🥩🥚 And evaluate your overall nutrition status. Fuel your body right to rebuild those building blocks! 🏗️",
        "Albumin": "Low albumin? Time to pump up your nutritional intake, especially focusing on protein! 💪 If issues persist, follow up with your doctor. Let's get those levels back up and running! 📈",
        "Globulin": "Low globulin? It's time to have a serious chat with your healthcare provider for further evaluation! 🗣️ Don't delay in understanding what's going on with your immune function! 🛡️",
        "ALP": "Low ALP (alkaline phosphatase) is a rare visitor and usually doesn't need a special treatment! 😉 Just monitor if other symptoms crash the party. Otherwise, enjoy the calm! 🎉",
        "ALT": "If your ALT is low and you're feeling symptoms of liver dysfunction, it's time for a reassessment! 🩺 Otherwise, your liver is likely just lounging around, enjoying a quiet day! 🛋️",
        "AST": "Low AST is generally a chill number, nothing to fret over! 😌 But if weird symptoms persist, a quick reassessment is always smart. Better safe than sorry! 🤔",
        "Bilirubin": "Low bilirubin? That's a 'no intervention needed' zone! ✅ Your body is processing things perfectly. Give yourself a pat on the back! 🙌",
        "Total Cholesterol": "Your total cholesterol is looking a bit low! 🧐 Make sure you're eating adequately and not showing any signs of malnutrition. Keep yourself well-nourished! 🍎",
        "LDL Cholesterol": "Low LDL? That's like winning the lottery for your heart! 💖 Keep doing whatever you're doing, it's generally favorable and a great sign! 🥳",
        "HDL Cholesterol": "If your HDL (the good cholesterol) is low, it's time to get active and make some dietary adjustments! 🏃‍♀️🥗 More physical activity and heart-healthy changes are key. Go get 'em! 💪",
        "Triglycerides": "Low triglycerides? Excellent! 🎉 If you're in overall good health, consider this a gold star for your efforts. Keep rocking that healthy lifestyle! ⭐",
        "TSH": "Low TSH? We need to play detective for hyperthyroidism and possibly run more thyroid function tests! 🕵️‍♀️ Your thyroid might be on overdrive, and we need to rein it in! 🚗💨",
        "Free T4": "Feeling tired and sluggish? Low free T4 might mean hypothyroidism! 😴 Consult an endocrinologist to get your thyroid back on track and boost your energy levels! 🩺",
        "PT": "A shorter PT time? That usually means no intervention needed! 👍 Your blood is clotting efficiently and quickly. You're a speedy clottin' machine! 💨",
        "INR": "If your INR is low, and you're on blood thinners, discuss with your doctor about your clotting speed. We want it just right – not too fast, not too slow! ⚖️",
        "aPTT": "A short aPTT could mean your blood is clotting too eagerly! ⚡ Additional tests might be needed if a 'hypercoagulable' state is suspected. Better safe than sorry when it comes to clotting! ⚠️",
        "HbA1c": "Super low HbA1c? Review your dietary choices to ensure adequate blood sugar control, or if the measurement is off. Let's find that perfect sweet spot for your body! 🎯",
        "Troponin": "Low troponin? That's exactly where we want it! ❤️ It means your heart is happy and healthy. Keep up the good work and give your heart a hug! 🤗",
        "CK": "Low CK? Don't even worry about it! 😌 It's typically not a concern at all. Your muscles are just playing it cool and collected. Chill out! 🧊",
        "CRP": "Low CRP? You're a health superstar! 🌟 Keep up that healthy lifestyle to keep inflammation levels down. You got this! 🧘‍♀️",
        "ESR": "A low ESR? That's generally a great sign for your body, suggesting minimal inflammation! 🎉 You're thriving, keep up the awesome work! 🌱"
    },
    "high": {
        "Hemoglobin": "Hemoglobin on the high side? Time for a medical check-up! 🩺 Stay hydrated like a desert survivor! 💧 And discuss if 'phlebotomy' (fancy word for blood letting) is needed. Don't wait! ",
        "RBC Count": "High RBCs? Could be polycythemia! 🚨 Further tests are highly recommended to find out why your body is making so many red blood cells. Are they overachievers? 🥇",
        "WBC Count": "WBCs acting wild? High count often means infection or inflammation! 🔥 Don't play doctor; consult your own doctor, stat! They'll know how to calm the troops! 🧑‍⚕️",
        "Platelet Count": "Platelets are too high! 🚨 This means increased clotting risks. A follow-up with a hematologist is a must to keep things flowing smoothly and avoid any sticky situations! 🩹",
        "PCV": "High PCV? Dehydration might be the culprit! 💧 Drink plenty of water and recheck. If it's still high, or you feel off, see a doctor – don't ignore your body's thirst signals! 🏜️",
        "MCV": "Big red blood cells? High MCV points to macrocytic anemia! 🥕 Get those vitamin B12 or folate levels checked and boosted! Your cells just need the right kind of fuel! 💊",
        "MCH": "High MCH? Your red cells are packed! 🎒 Further evaluation is recommended to understand why they're so full. What's the secret sauce making them so plump? 🤔",
        "MCHC": "High MCHC? This one's a bit of a head-scratcher and needs a direct chat with your healthcare provider for re-evaluation. Let's figure out this blood cell mystery together! 🤝",
        "RDW": "Your red blood cells have a wide range of sizes with high RDW! 📈 Follow up with more testing to understand this variability. Every cell tells a story, and we need to hear yours! 📖",
        "Neutrophils": "Your first responders, the neutrophils, are swarming! 🚨 Elevated neutrophils often scream 'bacterial infection' or serious inflammation. Time to find the culprit and kick it out! 🦠",
        "Lymphocytes": "Lymphocytes soaring? 🚀 Could be a viral infection or a long-term chronic condition setting in. Further evaluation is wise to pinpoint what's making them so active! 🕵️‍♀️",
        "Monocytes": "Elevated monocytes might signal chronic inflammation! 🔥 More tests could be required to understand what's been stirring in your body. Time to play detective and cool things down! 🔍",
        "Eosinophils": "High eosinophils? Are you battling allergies or hosting some unwelcome parasitic guests? 🤧🐛 Time for an eviction notice or an allergy check! Get rid of those freeloaders! ",
        "Basophils": "An increase in basophils? Time to chat with your doctor, as it could be a sign of chronic inflammation or allergic reactions! 🗣️ Get it checked and calm those reactive cells! 🎈",
        "Glucose": "Dial down the sugar intake! 🍫 Time for healthy habits to keep diabetes risks away! Your blood shouldn't taste like a candy store! 🍬",
        "Calcium": "Too much calcium? 🏗️ Let’s check if your parathyroid is throwing a party—monitor levels closely and consult a doctor! Your body needs balance! ⚖️",
        "Sodium": "High sodium? You're likely dehydrated! 🏜️ Drink plenty of water and monitor. If it's still high, or symptoms persist, consult a physician. Your body is thirsty! 💧",
        "Potassium": "Don’t let high potassium zap your heart! ⚡ Balance electrolytes and seek medical advice immediately if needed! This is a serious one, so don't delay! 🚨",
        "Chloride": "High chloride can mess with your body's metabolism! 🧪 Further investigation is needed to balance things out. It's like a scientific experiment to get your body back on track! 🔬",
        "Bicarbonate": "Elevated bicarbonate? This might signal metabolic alkalosis. 📈 Consult your healthcare provider to get your body's pH balance back to normal. No need for extreme swings! ⚖️",
        "BUN": "High BUN is a red flag for your kidneys! 🚩 Urgent diagnostic evaluation is necessary to understand kidney function. Don't delay in getting those important filters checked! 🩺",
        "Creatinine": "High creatinine is a flashing siren for impaired kidney function! 🚨 Get a doctor's advice *promptly*. Your kidneys are important, so give them the attention they deserve! 🏥",
        "Total Protein": "High total protein might indicate chronic inflammation or infection! 🔥 Additional tests may be warranted to find the source of this protein party. Time to investigate! 🔍",
        "Albumin": "Albumin riding high? 🚀 That usually means you're just a bit dehydrated! Chug some water and re-evaluate. Hydration is always key, even for your proteins! 💧",
        "Globulin": "Increased globulin levels? This might reflect chronic inflammation or infections! 🦠 Further evaluation is recommended to understand what's got your immune system working so hard! 🕵️‍♀️",
        "ALP": "High ALP (alkaline phosphatase) could indicate liver or bone disease! 🦴 Consult your doctor for more tests to pinpoint the problem. Let's get answers and get you feeling better! 🧪",
        "ALT": "Elevated ALT is a sign your liver might be inflamed or injured! 🤕 Seek medical evaluation to protect your precious liver. It works hard for you! 💪",
        "AST": "High AST? This suggests liver or muscle damage! 💪 Further testing is advised to find out what's causing the trouble. Don't let your body's engines run too hot! 🔥",
        "Bilirubin": "High bilirubin? This is a serious concern for liver dysfunction! 🚨 Urgent evaluation is recommended. Your liver is a vital organ, so give it immediate attention! ⚠️",
        "Total Cholesterol": "High cholesterol? This increases your heart risk! ❤️ Time for lifestyle changes (diet, exercise!) and possibly medication. Protect that ticker and keep it beating strong! 💪",
        "LDL Cholesterol": "High 'bad' LDL? This is a big risk factor for clogged arteries! 📉 Diet, exercise, and meds might be needed to bring it down. Your heart will thank you for it! 🙏",
        "HDL Cholesterol": "Super high HDL? While generally awesome and protective, extremely high values are rare and should be interpreted in the clinical context with your doctor. Still, mostly a win! 🏆",
        "Triglycerides": "High triglycerides are knocking at your heart's door, increasing risk! 🚪 Time for some serious lifestyle changes (diet, exercise!) and medication might be indicated. Let's close that door on heart disease! ❤️‍🩹",
        "TSH": "High TSH? Sounds like hypothyroidism! 😴 Consult an endocrinologist to get your thyroid sorted and energy back. Time to wake up that sleepy gland! ⏰",
        "Free T4": "High free T4? This might mean hyperthyroidism! 🚀 Further evaluation is recommended to understand why your thyroid is working overtime. Let's bring it back to a chill pace! 🧘‍♀️",
        "PT": "A prolonged PT means your blood is taking its sweet time to clot! ⏳ This could increase your bleeding risk, so be extra careful with sharp objects and activities! 🔪",
        "INR": "Your INR is super high! ⬆️ This means your blood is taking a long, long, LONG time to clot. If you're on thinners, review your anticoagulant management immediately with your doctor! 🚨",
        "aPTT": "A prolonged aPTT could indicate some quirky coagulation abnormalities! 🧐 Seek further testing to understand why your blood isn't clotting properly. No need for a race, but don't be a snail! 🐌",
        "HbA1c": "High HbA1c? This screams poor long-term blood sugar control! 🚨 Urgent lifestyle and medication review are crucial to get things in check. Your blood sugar's report card needs a major upgrade! 📈",
        "Troponin": "DANGER! Elevated troponin is a critical sign of heart muscle injury! 🚨 Seek immediate medical attention. This is an emergency you can't ignore! ❤️‍🩹",
        "CK": "Your CK is high! 📈 This points to muscle damage. What have you been lifting? 😉 Or perhaps something more serious needs a check. Get those muscles looked at! 💪",
        "CRP": "High CRP? This is a clear sign of systemic inflammation somewhere in your body! 🔥 Consult your doctor for further evaluation to find the source of the fire and put it out! 🚒",
        "ESR": "High ESR? This is a non-specific alarm for inflammation! 🔔 Additional tests may be needed to pinpoint what's causing the elevated level. Let's find the root cause of the body's alert! 🕵️‍♀️"
    }
}

# Common OCR mistakes and corrections
# Updated test_name_corrections: mapping common mis-spellings or abbreviations
test_name_corrections = {
    # Hemoglobin variants
    "hemoglobn": "Hemoglobin",
    "hemaglabia": "Hemoglobin",
    "hb": "Hemoglobin",
    "hemoglobin": "Hemoglobin",
    "hemoglobin level": "Hemoglobin",
    
    # Packed Cell Volume (PCV) variants
    "pcv": "PCV",
    "packed cell volume": "PCV",
    "packedcellvolume": "PCV",
    "pct": "PCV",  # sometimes use percent cell volume abbreviation
    
    # Red Blood Cell Count variants
    "rbc": "RBC Count",
    "rbc count": "RBC Count",
    "red blood cells": "RBC Count",
    "red blood cell count": "RBC Count",
    
    # White Blood Cell Count variants
    "wbc": "WBC Count",
    "wbc count": "WBC Count",
    "white blood cells": "WBC Count",
    "white blood cell count": "WBC Count",
    
    # Platelet Count variants
    "platelet": "Platelet Count",
    "platelets": "Platelet Count",
    "platelet count": "Platelet Count",
    "plt": "Platelet Count",
    
    # Mean corpuscular volume (MCV)
    "mcv": "MCV",
    "mean corpuscular volume": "MCV",
    "mcv value": "MCV",
    
    # Mean corpuscular hemoglobin (MCH)
    "mch": "MCH",
    "mean corpuscular hemoglobin": "MCH",
    "mean chol": "MCH",
    
    # Mean corpuscular hemoglobin concentration (MCHC)
    "mchc": "MCHC",
    "mean corpuscular hemoglobin concentration": "MCHC",
    "corpuscular hemoglobin": "MCHC",
    
    # Red cell distribution width (RDW)
    "rdw": "RDW",
    "red cell distribution width": "RDW",
    "red cell dist width": "RDW",
    
    # Neutrophils variants
    "neutrophils": "Neutrophils",
    "neutrophil": "Neutrophils",
    "neutrophls": "Neutrophils",
    "neutro": "Neutrophils",
    
    # Lymphocytes variants
    "lymphocytes": "Lymphocytes",
    "lymphocyte": "Lymphocytes",
    "lymph": "Lymphocytes",
    "lymphcytes": "Lymphocytes",
    
    # Monocytes variants
    "monocytes": "Monocytes",
    "monocyte": "Monocytes",
    "moncytes": "Monocytes",
    "monos": "Monocytes",
    
    # Eosinophils variants
    "eosinophils": "Eosinophils",
    "eosin": "Eosinophils",
    "eos": "Eosinophils",
    "eosinphils": "Eosinophils",
    
    # Basophils variants
    "basophils": "Basophils",
    "baso": "Basophils",
    "basphils": "Basophils",
    
    # Glucose and metabolic panel
    "glucose": "Glucose",
    "blood sugar": "Glucose",
    
    "calcium": "Calcium",
    "sodium": "Sodium",
    "potassium": "Potassium",
    "chloride": "Chloride",
    "bicarbonate": "Bicarbonate",
    "hco3": "Bicarbonate",
    
    "bun": "BUN",
    "blood urea nitrogen": "BUN",
    "urea": "BUN",
    
    "creatinine": "Creatinine",
    "creat": "Creatinine",
    
    # Protein panel
    "total protein": "Total Protein",
    "totalprotein": "Total Protein",
    
    "albumin": "Albumin",
    "alb": "Albumin",
    
    "globulin": "Globulin",
    
    # Liver enzymes
    "alp": "ALP",
    "alkaline phosphatase": "ALP",
    
    "alt": "ALT",
    "alanine aminotransferase": "ALT",
    
    "ast": "AST",
    "aspartate aminotransferase": "AST",
    
    "bilirubin": "Bilirubin",
    "bili": "Bilirubin",
    
    # Lipid Panel
    "total cholesterol": "Total Cholesterol",
    "cholesterol": "Total Cholesterol",
    "total chol": "Total Cholesterol",
    
    "ldl": "LDL Cholesterol",
    "ldl cholesterol": "LDL Cholesterol",
    "bad chol": "LDL Cholesterol",
    
    "hdl": "HDL Cholesterol",
    "hdl cholesterol": "HDL Cholesterol",
    "good chol": "HDL Cholesterol",
    
    "triglycerides": "Triglycerides",
    "trigs": "Triglycerides",
    
    # Thyroid function
    "tsh": "TSH",
    "thyroid stimulating hormone": "TSH",
    
    "free t4": "Free T4",
    "t4": "Free T4",
    "thyroxine": "Free T4",
    
    # Coagulation tests
    "pt": "PT",
    "prothrombin time": "PT",
    
    "inr": "INR",
    "international normalized ratio": "INR",
    
    "apt": "aPTT",
    "aptt": "aPTT",
    "activated partial thromboplastin time": "aPTT",
    
    "hba1c": "HbA1c",
    "hb a1c": "HbA1c",
    "hemoglobin a1c": "HbA1c",
    "glycated hemoglobin": "HbA1c",
    
    # Cardiac Enzymes
    "troponin": "Troponin",
    
    "ck": "CK",
    "creatine kinase": "CK",
    
    # Inflammatory Markers
    "crp": "CRP",
    "c reactive protein": "CRP",
    "c-reactive protein": "CRP",
    
    "esr": "ESR",
    "erythrocyte sedimentation rate": "ESR"
}


def adjust_value(test, raw_value):
    """
    Adjusts raw_value for a given test. If the OCR-detected value is
    off by a multiplication factor (e.g., missing a decimal point), this
    function will try to scale it down by candidate divisors. It accepts
    a candidate if:
      - It falls within the strict reference range; OR
      - It is within a defined relative tolerance of the expected mean.
    """
    # Look up the reference range for the test from the updated medical_tests dict
    if test not in medical_tests:
        return raw_value  # no adjustment if no reference available

    low, high = medical_tests[test]
    mean_val = (low + high) / 2.0
    # If the raw_value already lies in the acceptable range, return it as is.
    if low <= raw_value <= high:
        return raw_value

    # Define candidate divisors and a tolerance level (e.g., 20% deviation from mean)
    candidate_divisors = [10, 100, 1000]
    tolerance = 0.20  # 20%

    for divisor in candidate_divisors:
        candidate = raw_value / divisor
        # Check if candidate lies strictly within the reference range ...
        if low <= candidate <= high:
            return candidate
        # ... Or check if the candidate is close enough to the expected mean.
        elif abs(candidate - mean_val) / mean_val < tolerance:
            return candidate

    # If no candidate fits our criteria, return the raw_value as a fallback.
    return raw_value


def extract_text(image_path):
    """Extract text from the image report using OCR."""
    img = Image.open(image_path)
    return pytesseract.image_to_string(img)

def clean_text(raw_text):
    """Remove unwanted characters and extra newlines from OCR output."""
    text = re.sub(r'[^\w\s:/.-]', '', raw_text)
    return re.sub(r'\n+', '\n', text)

def correct_test_name(test_name, valid_tests):
    # Ignore tokens with no word characters (e.g., '-')
    if not re.search(r'\w', test_name):
        return None
    if test_name.lower() in test_name_corrections:
        return test_name_corrections[test_name.lower()]
    best_match, score = process.extractOne(test_name, valid_tests)
    if score > 85:
        return best_match
    return None

from fuzzywuzzy import process
import re

def correct_test_name(test_name, valid_tests):
    """
    Correct test names with an expanded dictionary for common variations,
    abbreviations, full forms, and mis-spellings. The function cleans the token,
    checks our dictionary, and if not found, falls back to fuzzy matching.
    """
    # Remove punctuation, extra spaces, and convert to lowercase
    token = re.sub(r'[^\w\s]', '', test_name).strip().lower()
    if not token:
        return None
    
    # If the token is found in our expanded corrections dictionary, return its mapping
    if token in test_name_corrections:
        return test_name_corrections[token]
    
    # Otherwise, perform fuzzy matching on the provided valid_tests list
    best_match, score = process.extractOne(token, valid_tests)
    if score >= 85:
        return best_match
    return None

def extract_health_metrics(text):
    """
    Extracts health metrics from the cleaned text.
    Processes the text line by line so that a candidate test name (even mis-spelled) 
    is accepted only when a number is found on the same line.
    """
    data = {}
    lines = text.splitlines()
    
    for line in lines:
        # Skip empty lines
        line = line.strip()
        if not line:
            continue
        
        for token in line.split():
            corrected = correct_test_name(token, list(medical_tests.keys()))
            if corrected and corrected not in data:
                # Capture the number that appears in the same line after the test name.
                pattern = fr'\b{corrected}\b.*?([\d,.]+)'
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    try:
                        # Get raw value from OCR output
                        raw_value = float(match.group(1).replace(',', ''))
                        # Adjust the value if necessary using our helper function.
                        adjusted_value = adjust_value(corrected, raw_value)
                        data[corrected] = adjusted_value
                    except ValueError:
                        continue
    return data

def analyze_health_data(data):
    """
    Compare extracted metrics with reference ranges and generate insights.
    
    For each test, it reports whether the value is normal, low, or high, and includes
    an explanation and recommendation if it is abnormal.
    """
    insights = {}
    for test, value in data.items():
        if test in medical_tests:
            low, high = medical_tests[test]
            if value < low:
                condition = "low"
            elif value > high:
                condition = "high"
            else:
                insights[test] = f"✅ Normal ({value} {test})"
                continue

            explanation = explanations.get(condition, {}).get(test, "Further analysis needed.")
            recommendation = recommendations.get(condition, {}).get(test, "Consult a healthcare professional.")
            insights[test] = (f"⚠️ {condition.capitalize()} ({value} {test}) - {explanation}\n"
                              f"🛑 Recommendation: {recommendation}")
    return insights

def format_health_report(insights):
    """Convert insights to HTML format for web display."""
    html_report = "<div class='report'>"
    for test, result in insights.items():
        if 'Normal' in result:
            html_report += f"<p class='normal'>✅ {test}: {result.replace('✅', '')}</p>"
        else:
            html_report += f"<p class='abnormal'>⚠️ {test}: {result.replace('⚠️', '')}</p>"
    html_report += "</div>"
    return html_report


def generate_plot(data):
    """Generate a bar chart and return it as a base64 image."""
    # # Use Agg backend which is thread-safe
    # import matplotlib
    # matplotlib.use('Agg')
    # import matplotlib.pyplot as plt
    
    plt.switch_backend('Agg')

    tests = list(data.keys())
    values = list(data.values())
    colors = []
    for test, value in data.items():
        low, high = medical_tests.get(test, (None, None))
        if low is not None and high is not None:
            if value < low:
                colors.append('blue')
            elif value > high:
                colors.append('red')
            else:
                colors.append('green')
        else:
            colors.append('gray')
    
    plt.figure(figsize=(10, 5))
    plt.bar(tests, values, color=colors)
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Value")
    plt.title("Medical Test Results")
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plot_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close('all')
    return plot_data
# ===== END OF NEW FUNCTION =====

# ===== FLASK ROUTES (KEEP THIS AT THE BOTTOM) =====
# 

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'GET':
        return render_template('index.html')
    
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    try:
        # Process image directly from memory
        img = Image.open(io.BytesIO(file.read()))
        raw_text = pytesseract.image_to_string(img)
        cleaned = clean_text(raw_text)
        health_data = extract_health_metrics(cleaned)
        insights = analyze_health_data(health_data)
        plot = generate_plot(health_data)
        
        return jsonify({
            "insights": insights,
            "plot": plot,
            "health_data": health_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # # Development (keep this for testing)
    # app.run(debug=True)
    
    #For production (comment out when developing):
    from waitress import serve
    port = int(os.environ.get("PORT",10000))
    serve(app, host="0.0.0.0", port=10000)


# #For easy switching between development/production, you can use:
# if __name__ == '__main__':
#     if os.environ.get('PRODUCTION'):
#         from waitress import serve
#         serve(app, host="0.0.0.0", port=5000)
#     else:
#         app.run(debug=True)
