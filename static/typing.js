const typewriter = document.getElementById("typing_effect");
const words = [
  /*{ text: "Craving something but also lazy enough??", color: "white" },
  */{ text: "Time for IIITeats", color: "white",  },
 /* { text: "IIITeats", color: "rgb(195,139,91)" },
  { text: "IIITeats", color: "rgb(243,200,81)" },*/
]; // List of words to be displayed
let currentWordIndex = 0; // Index of the current word being typed
let currentCharIndex = 0; // Index of the current character being typed

function typeWriter() {
  if (currentCharIndex < words[currentWordIndex].text.length) {
    const char = words[currentWordIndex].text.charAt(currentCharIndex);
    const color = words[currentWordIndex].color;
    const span = document.createElement("span");
    span.style.color = color;
    span.innerHTML = char;
    typewriter.appendChild(span);
    currentCharIndex++;
    setTimeout(typeWriter, 150); // delay between each character
  } else {
    setTimeout(function () {
      deleteText(words[currentWordIndex].text);
    }, 1200);
  }
}

function deleteText(word) {
  if (currentCharIndex > 0) {
    typewriter.removeChild(typewriter.lastChild);
    currentCharIndex--;
    setTimeout(function () {
      deleteText(word);
    }, 70); // delay between each character
  } else {
    currentWordIndex = (currentWordIndex + 1) % words.length; // move to next word
    currentCharIndex = 0; // reset character index
    setTimeout(typeWriter, 800);
  }
}
typeWriter();