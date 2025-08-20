// Toggle comments
document.querySelectorAll('.comment-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const postId = this.dataset.postId;
        const commentsDiv = document.getElementById('comments-' + postId);
        commentsDiv.style.display = commentsDiv.style.display === 'none' ? 'block' : 'none';
    });
});

// Add comment via AJAX
document.querySelectorAll('.comment-form').forEach(form => {
    form.addEventListener('submit', function(e){
        e.preventDefault();
        const postId = this.dataset.postId;
        const input = this.querySelector('input[name="content"]');
        const content = input.value.trim();
        if(!content) return;

        fetch("/add_comment/", {  // use your URL
            method: 'POST',
            headers: {
                'X-CSRFToken': '{{ csrf_token }}',
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: 'post_id=' + postId + '&content=' + encodeURIComponent(content)
        })
        .then(res => res.json())
        .then(data => {
            const commentsList = document.querySelector('#comments-' + postId + ' .comments-list');
            const newComment = document.createElement('div');
            newComment.classList.add('d-flex','align-items-start','mb-2','comment-item');
            newComment.innerHTML = `
                <img src="${data.profile_image || '/static/profile_pics/default.jpg'}" class="comment-avatar me-2" style="width:32px;height:32px;border-radius:50%;">
                <div class="comment-content bg-light rounded px-2 py-1">
                    <div class="fw-semibold">${data.username}</div>
                    <div>${data.content}</div>
                    <small class="text-muted">just now</small>
                </div>
            `;
            commentsList.appendChild(newComment);
            input.value = '';
            const commentBtn = document.querySelector('.comment-btn[data-post-id="' + postId + '"] .comment-count');
            if(commentBtn){ commentBtn.textContent = data.total_comments; }
        })
        .catch(console.error);
    });
});
