document.addEventListener('DOMContentLoaded', function () {
    const input = document.querySelector('#tag-input');
    const tagContainer = document.querySelector('#selected-tags');
    const suggestionBox = document.createElement('div');

    suggestionBox.id = 'tag-suggestions';
    suggestionBox.className = 'list-group position-absolute shadow-sm';
    suggestionBox.style.zIndex = '1000';
    suggestionBox.style.width = input.offsetWidth + 'px';
    suggestionBox.style.display = 'none';
    input.parentNode.appendChild(suggestionBox);

    let selectedTags = input.value ? input.value.split(',').map(t => t.trim()) : [];

    function renderTags() {
        tagContainer.innerHTML = '';
        selectedTags.forEach(tag => {
            const badge = document.createElement('span');
            badge.className = 'badge bg-success me-1';
            badge.innerHTML = `${tag} <span class="ms-1" style="cursor:pointer;" data-tag="${tag}">&times;</span>`;
            tagContainer.appendChild(badge);
        });
        input.value = selectedTags.join(', ');

        tagContainer.querySelectorAll('[data-tag]').forEach(span => {
            span.onclick = function () {
                const tagToRemove = this.getAttribute('data-tag');
                selectedTags = selectedTags.filter(t => t !== tagToRemove);
                renderTags();
            };
        });
    }

    function showSuggestions(suggestions) {
        suggestionBox.innerHTML = '';
        suggestions.forEach(tag => {
            const item = document.createElement('button');
            item.type = 'button';
            item.className = 'list-group-item list-group-item-action';
            item.textContent = tag;
            item.onclick = function () {
                if (!selectedTags.includes(tag)) {
                    selectedTags.push(tag);
                    renderTags();
                    suggestionBox.style.display = 'none';
                    input.value = '';
                    input.focus();
                }
            };
            suggestionBox.appendChild(item);
        });
        suggestionBox.style.display = suggestions.length ? 'block' : 'none';
    }

    input.addEventListener('input', function () {
        const query = input.value.trim();
        if (query.length === 0) {
            suggestionBox.style.display = 'none';
            return;
        }

        fetch(`/tags/suggestions/?term=${encodeURIComponent(query)}&context=${input.dataset.context || ''}`)
            .then(response => response.json())
            .then(data => {
                const filtered = data
                    .filter(tag => !selectedTags.includes(tag))
                    .slice(0, 10);
                showSuggestions(filtered);
            })
            .catch(err => console.error('Error fetching tag suggestions:', err));
    });

    input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            const tag = input.value.trim().replace(/,$/, '');
            if (tag && !selectedTags.includes(tag)) {
                selectedTags.push(tag);
                renderTags();
                input.value = '';
                suggestionBox.style.display = 'none';
            }
        }
    });

    document.addEventListener('click', function (e) {
        if (!suggestionBox.contains(e.target) && e.target !== input) {
            suggestionBox.style.display = 'none';
        }
    });

    renderTags();
});
