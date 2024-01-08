const college_city_select = document.getElementById("college_city");
const college_select = document.getElementById("college_id");
const college_select_input = document.getElementById("college_id_input");

function stateSelected() {
    const college_state = document.getElementById("college_state").value;
    college_select.hidden = true;
    if (college_state === "0") {
        college_city_select.hidden = true;
    } else {
        fetch(`/users/fetch_colleges/?state=${college_state}`)
            .then(response => response.json())
            .then(data => {
                college_city_select.innerHTML = '<option value="0" selected disabled>Select College City</option>';
                data.forEach(city => {
                    college_city_select.innerHTML += `<option value="${city}">${city}</option>`;
                });
            });
        college_city_select.hidden = false;
    }
}

function citySelected() {
    const college_state = document.getElementById("college_state").value;
    const college_city = document.getElementById("college_city").value;
    if (college_city === "0") {
        college_select_input.hidden = true;
    } else {
        fetch(`/users/fetch_colleges/?state=${college_state}&city=${college_city}`)
            .then(response => response.json())
            .then(data => {
                college_select.innerHTML = '<option value="0" selected disabled>Select College</option>';
                data.forEach(college => {
                    college_select.innerHTML += `<option value="${college.college_id}">${college.college_name}</option>`;
                });
            });
        college_select_input.hidden = false;
    }
}

function checkIfCollegeIDinDatalist() {
    const college_id = document.getElementById("college_id_input").value;
    const college_id_list = document.getElementById("college_id");
    if (!college_id_list.innerHTML.includes(college_id)) {
        document.getElementById("college_id_input").value = "";
    }
}