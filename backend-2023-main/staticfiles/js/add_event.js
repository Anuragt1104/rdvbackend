function setTags() {
    const tags = document.getElementById("tags");
    const selectedTags = document.getElementsByClassName("selected-tag");
    tags.value = "";
    for (let i = 0; i < selectedTags.length; i++) {
        tags.value += selectedTags[i].innerText + ",";
    }
    tags.value = tags.value.slice(0, -1);
}

function handleTag(e) {
    if (e.classList.contains('selected-tag')) {
        e.classList.remove('selected-tag')
        setTags()
    } else {
        e.classList.add('selected-tag')
        setTags()
    }
}

function create_tag_modal() {
    const modal = document.getElementsByClassName("create-tag-modal")[0];
    modal.style.display = "flex";
}

function create_tag() {
    const modal = document.getElementsByClassName("create-tag-modal")[0];
    const tag_name = document.getElementById("new-tag-name");
    if (tag_name.value === "") {
        alert("Tag name cannot be empty");
        return;
    }
    modal.style.display = "none";
    const tagContainer = document.getElementsByClassName("tag-container")[0];
    var tagCreate = document.getElementsByClassName("create-tag")[0];
    tagCreate.remove();
    const newTag = `<p class="tag selected-tag" onclick="handleTag(this)">${tag_name.value}</p>
    <p class="tag create-tag" onclick="create_tag_modal()">Create Tag</p>`
    tag_name.value = "";
    tagContainer.insertAdjacentHTML('beforeend', newTag);
    
    setTags()
}

window.onclick = function (event) {
    const modal = document.getElementsByClassName("create-tag-modal")[0];
    if (event.target === modal) {
        modal.style.display = "none";
    }
}