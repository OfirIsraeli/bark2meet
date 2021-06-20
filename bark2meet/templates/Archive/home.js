let map;
let all_markers = [];
var pos;
function initMap() {
  map = new google.maps.Map(document.getElementById("map"), {
    center: { lat: 31.771959, lng: 35.217018 },
    zoom: 15,
  });
  infoWindow = new google.maps.InfoWindow();
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        pos = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        };

        const URL = "/home";
        const xhr = new XMLHttpRequest();
        let sender = JSON.stringify([position.coords.latitude, position.coords.longitude]);
        xhr.open("POST", URL);
        xhr.send(sender);

        //infoWindow.setPosition(pos);
        //infoWindow.setContent("Location found.");
        //infoWindow.open(map);
        map.setCenter(pos);
      },
      () => {
        handleLocationError(true, infoWindow, map.getCenter());
      }
    );
  } else {
    // Browser doesn't support Geolocation
    handleLocationError(false, infoWindow, map.getCenter());
    map.setCenter({
      lat: 31.771959,
      lng: 35.217018,
    });
  }
  initializeMarkers();
}

function UpdateUserLocation() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition((position) => {
      var pos = {
        lat: position.coords.latitude,
        lng: position.coords.longitude,
      };

      const URL = "/update_user_location";
      const xhr = new XMLHttpRequest();
      let sender = JSON.stringify([position.coords.latitude, position.coords.longitude]);
      xhr.open("POST", URL);
      xhr.send(sender);
    });
  }
}

function initializeMarkers() {
  fetch("/api/locations")
    .then(function (response) {
      return response.json();
    })
    .then(function (all_locations) {
      addMarkers(all_locations);
    });
}

function addMarkers(all_locations) {
  for (let i = 0; i < all_locations.length; i++) {
    const marker = new google.maps.Marker({
      position: new google.maps.LatLng(all_locations[i].pos_x, all_locations[i].pos_y),
      icon: all_locations[i].image,
      map: map,
    });
    all_markers.push(marker);

    var infoWindow = NaN;
    // green\orange person marker options
    if (all_locations[i].privacy === "green" || all_locations[i].privacy === "orange") {
      // open infowindow
      var infoWindow = new google.maps.InfoWindow({
        content: createPopupMarker(all_locations[i]),
      });
    }

    // red person marker options
    else {
      // open infowindow
      var infoWindow = new google.maps.InfoWindow({
        content: createPopupMarker(all_locations[i]),
        maxWidth: 250,
      });
    }

    marker.addListener("click", function () {
      // DISABLE LOCATION UPDATE
      shouldUpdateLocation = false;
      infoWindow.setContent(infoWindow.content);
      infoWindow.open(map, marker);
      map.setZoom(18);
      map.setCenter(marker.getPosition());
    });

    infoWindow.addListener("closeclick", function () {
      shouldUpdateLocation = true;
    });
  }
}

function updateMarkers() {
  fetch("/api/locations")
    .then(function (response) {
      return response.json();
    })
    .then(function (all_locations) {
      console.log(all_locations[0]);
      // remove all users locations
      for (let i = 0; i < all_locations.length; i++) {
        all_markers[i].setMap(null);
      }
      all_markers = [];

      // update all users locations
      addMarkers(all_locations);
    });
}
function mapGender(genderNumber) {
  switch (genderNumber) {
    case 1:
      return "Male";
    case 2:
      return "Female";
    case 3:
      return "Unidentified";
  }
}
function getFirstName(fullName) {
  return fullName.split(/(\s+)/)[0];
}
function removeBaseAddress(address) {
  return address.slice(10);
}

function createPopupMarker(userInfo) {
  if (userInfo.privacy === "green") {
    console.log(userInfo);
    return (
      '<div id="infoContentGreen">' +
      '<div class="container1">' +
      '<h1 class="popup-header">New friends for ' +
      userInfo.dog_name +
      "  & You,</h1>" +
      '<h1 class="popup-header">check them out!</h1>' +
      "<div>" +
      '<img src="' +
      removeBaseAddress(userInfo.dog_image) +
      '">' +
      "</div>" +
      '<h2 class="popup-header2Name">' +
      getFirstName(userInfo.full_name) +
      " & " +
      userInfo.dog_name +
      "</h2>" +
      '<h2 class="popup-header2">Only ' +
      "greenInformation.gDistance" +
      " away!</h2>" +
      '<div class="infoBox">' +
      '<div class="popup-owner-side">' +
      "<p>" +
      mapGender(userInfo.gender) +
      "</p>" +
      "<p>" +
      mapGender(userInfo.gender) +
      " years old</p>" +
      "</div>" +
      '<div class="vl"></div>' +
      '<div class="popup-dog-side">' +
      "<p>" +
      mapGender(userInfo.dog_gender) +
      "</p>" +
      "<p>" +
      userInfo.dog_age +
      " years old</p>" +
      "</div>" +
      "</div>" +
      "<a href=" +
      "greenInformation.gOtherProfile" +
      'class="a">See full profile  <img src="static/arrowside.png"></a>' +
      '<div class="iconsBox">' +
      '<i><img id="addFriend" src="static/addfriendgreen.png"></i>' +
      '<i><img src="static/navigategreen.png"></i>' +
      '<i><img src="static/pokegreen.png"></i>' +
      "</div>" +
      "</div>" +
      "</div>"
    );
  }

  if (userInfo.privacy === "orange") {
    return (
      '<div id="infoContentOrange">' +
      '<div class="container2">' +
      '<h1 class="popup-header">Your friends are out!</h1>' +
      '<h1 class="popup-header">Join their walk</h1>' +
      "<div>" +
      '<img src="Pics/lisa_dog.svg">' +
      "</div>" +
      '<h2 class="popup-header2Name">' +
      orangeInformation.oOtherOwnerName +
      " & " +
      orangeInformation.oOtherDogName +
      "</h2>" +
      '<h2 class="popup-header2">Only' +
      orangeInformation.oDistance +
      "  away!</h2>" +
      "<a href=" +
      orangeInformation.oOtherProfile +
      'class="a">See full profile  <img src="Pics/arrowside.png"></a>' +
      '<div class="iconsBox">' +
      '<i><img src="Pics/navigateorange.png"></i>' +
      '<i><img src="Pics/pokeorange.png"></i>' +
      "</div>" +
      "</div>" +
      "</div>"
    );
  }

  return (
    '<div id="infoContentRed">' +
    '<div class="container3">' +
    '<h1 class="popup-header">Pay attention:</h1>' +
    '<h1 class="popup-header">A' +
    redInformation.rOtherDogsBreed +
    "  is nearby...</h1>" +
    "<div>" +
    "<p class='popup-dog-side'>These two are on private mode. so you can't reach out this time.</p>" +
    "</div>" +
    "</div>" +
    "</div>"
  );
}

let shouldUpdateLocation = true;
const interval = setInterval(function () {
  if (shouldUpdateLocation) {
    UpdateUserLocation();
    updateMarkers();
  }
}, 5000);

function openChatWithTarget(userName) {
  let chatDiv = document.getElementById("chat");
  let chatHeader = document.getElementById("chatHeader");
  chatHeader.innerHTML = "Chat With " + userName;
  console.log("Chatting with: " + userName);

  chatDiv.style.display = "block";
}

function handleLocationError(browserHasGeolocation, infoWindow, pos) {
  infoWindow.setPosition(pos);
  infoWindow.setContent(
    browserHasGeolocation
      ? "Error: The Geolocation service failed."
      : "Error: Your browser doesn't support geolocation."
  );
  infoWindow.open(map);
}
