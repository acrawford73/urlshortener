// Randomizing button text

const button = document.getElementById('randomTextButton');
const buttonTexts = [
	"Shrink!",
	"Shrink it!",
	"Shrink that link!",
	"Give'r!",
	"Shrink that mofo!",
	"Shrink it or link it!",
	"Shrink link clowns that come around!",
	"Tell that MF link to chill!",
	"Shrink it and dig it...",
	"I ain't playin'",
	"Ain't nobody got time for no MF long links",
	"I ain't a player, I just link a lot",
	"I hate big links I cannot lie",
	"Ain't gonna get a long link outta me",
	"Zooma zoom zoom link shaker",
];

// Set random button text on page load
const randomIndex = Math.floor(Math.random() * buttonTexts.length);
button.textContent = buttonTexts[randomIndex];
