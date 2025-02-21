// server.js

const express = require('express');  // Import the Express library to create a web server
const bodyParser = require('body-parser'); // Import the body-parser library to parse incoming JSON requests
const OpenAI = require("openai");  // Import the OpenAI library to interact with the Moonshot API
require("dotenv").config();

// Create an Express app instance
const app = express();
const PORT = process.env.PORT || 3000;  // Define the port number, using environment variable or defaulting to 3000

// Middleware: Use body-parser to parse JSON request bodies
app.use(bodyParser.json());

// Middleware: Serve static files under the public folder (e.g., HTML, CSS, JavaScript files)
app.use(express.static('public'));

// Initialize the Kimi Moonshot API client with the API key and base URL
const client = new OpenAI({
    apiKey: process.env.MOONSHOT_API_KEY,  // Load API key from environment variables (SECURITY FIX)
    baseURL: "https://api.moonshot.cn/v1",  // Set the API base URL
});

// Define an API route to refine emotions based on user input
app.post('/refineEmotion', async (req, res) => {
    try {
        const { mainEmotion, emotionDetail } = req.body;  // Extract data from the request body
        
        // Validate that mainEmotion is provided; return an error if missing
        if (!mainEmotion) {
            return res.status(400).json({ error: "mainEmotion is required" });
        }

        // If emotionDetail is provided, refine the emotion using the AI model
        if (emotionDetail && emotionDetail.trim().length > 0) {
            // Create a prompt in Chinese to guide the AI in selecting the best matching emotion
            const prompt = `请根据以下描述细化情感，并在以下情感列表中选择最匹配的情感，仅回复情感名称：
情感描述: "${emotionDetail}"
主要情感: "${mainEmotion}"
情感列表: Joy, Love, Devotion, Tender feelings, Suffering, Weeping, High spirits, Low spirits, Anxiety, Grief, Dejection, Despair, Anger, Hatred, Disdain, Contempt, Disgust, Guilt, Pride, Helplessness, Patience, Affirmation, Negation, Surprise, Fear, Self-attention, Shyness, Modesty, Blushing, Reflection, Meditation, Ill-temper, Sulkiness, Determination.`;

            // Call the Moonshot AI API to generate a refined emotion response
            const completion = await client.chat.completions.create({
                model: "moonshot-v1-8k",  // Use the Moonshot AI model
                messages: [
                    { 
                        role: "system", 
                        content: "你是 Kimi，由 Moonshot AI 提供的人工智能助手，擅长中文和英文的对话，回答安全、准确且有帮助。" 
                    },
                    { 
                        role: "user", 
                        content: prompt  // Pass the prompt to the AI
                    }
                ],
                temperature: 0.3,  // Set response randomness (lower values make responses more deterministic)
                max_tokens: 20  // Limit the response length to 20 tokens
            });

            // Extract the refined emotion from the API response
            const refinedEmotion = completion.choices[0].message.content.trim();
            return res.json({ emotion: refinedEmotion });  // Send the refined emotion as JSON response
        } else {
            // If no detailed description is provided, return the main emotion directly
            return res.json({ emotion: mainEmotion });
        }
    } catch (error) {
        console.error("Error refining emotion:", error);  // Log errors for debugging
        return res.status(500).json({ error: "Failed to refine emotion" });  // Return a 500 error response
    }
});

// Start the Express server and listen for incoming requests
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);  // Log server startup message
});
