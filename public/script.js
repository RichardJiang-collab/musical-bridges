// public/script.js

document.getElementById("submitBtn").addEventListener("click", async () => { // Add event listener to the submit button
    const mainEmotion = document.getElementById("mainEmotion").value; // Get the value of the main emotion input
    const emotionDetail = document.getElementById("emotionDetail").value.trim(); // Get the value of the emotion detail input and trim whitespace
  
    const payload = { mainEmotion }; // Create a payload object with the main emotion
    if (emotionDetail.length > 0) { // If emotion detail is not empty
      payload.emotionDetail = emotionDetail; // Add emotion detail to the payload
    }
  
    try {
      const response = await fetch("/refineEmotion", { // Send a POST request to the /refineEmotion endpoint
        method: "POST", // Specify the request method as POST
        headers: { "Content-Type": "application/json" , "X-myName" : "Richard Jiang"}, // Set the request headers
        body: JSON.stringify(payload) // Convert the payload object to a JSON string
      });
      const data = await response.json(); // Parse the JSON response
      
      document.getElementById("result").innerHTML = `
        <h2>Final Emotion: ${data.emotion}</h2>
        <p>Now recommending music based on this emotion...</p>
      `;
      
      // Here you could also call your music recommendation logic, passing data.emotion as a parameter.
      
    } catch (err) { // Handle any errors that occur during the fetch
      console.error("Error fetching recommendation:", err); // Log the error to the console
      document.getElementById("result").innerHTML = `<p>Error: ${err.message}</p>`; // Display the error message in the result element
    }
  });
