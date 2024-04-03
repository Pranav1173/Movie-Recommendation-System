document.addEventListener('DOMContentLoaded', () => {
    const movies = [
        {
            title: "The Shawshank Redemption",
            year: "1994",
            description: "Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.",
            imageFileName: "assets/TheShawshankRedemption.jpg"
        },
        {
            title: "Inception",
            year: "2010",
            description: "A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a CEO.",
            imageFileName: "assets/inception.jpg"
        },
        {
            title: "The Dark Knight",
            year: "2008",
            description: "When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.",
            imageFileName: "assets/the_dark_knight.jpg"
        }
        // Add more movie objects here
    ];

    const movieList = document.getElementById('movie-list');
    movies.forEach(movie => {
        const movieEl = document.createElement('div');
        movieEl.classList.add('movie');
        movieEl.innerHTML = `
            <img src="${movie.imageFileName}" alt="Movie Poster" class="movie__img">
            <h3>${movie.title} (${movie.year})</h3>
            <p>${movie.description}</p>
        `;
        movieList.appendChild(movieEl);
    });
});
