$(document).ready(function () {
  var socket = io.connect("/");

  var socket_messages = io("/messages");

  socket_messages.on("from flask", function (msg) {
    alert(msg);
  });

  socket.on("server orginated", function (msg) {
    alert(msg);
  });

  var private_socket = io("/private");
  private_socket.emit("email");


  const APP_NAME = "Bark2Meet"
  // ------------------------------- FRIENDS WALK EVENTS -------------------------------
  private_socket.on("new_friend_walk", function (data) {
    $("#notification_link").css('color', 'red')
    localStorage.setItem("newNotification", true);
    createNotification(APP_NAME, data.username + " is on the go!");
  });

  // ------------------------------- FRIENDS REQUEST EVENTS -------------------------------

  private_socket.on("new_friend_request", function (data) {
    $("#regular_notification_bell").hide()
    $("#new_notification_bell").show()
    localStorage.setItem("newNotification", true);
    createNotification(APP_NAME, data.username + " has sent you a friend request");
  });

  private_socket.on("friend_request_approve", function (data) {
    $("#regular_notification_bell").hide()
    $("#new_notification_bell").show()
    localStorage.setItem("newNotification", true);
    createNotification(APP_NAME, data.username + " has accepted your friend request");
  });

  // ------------------------------- EVENT REQUESTS -------------------------------

  private_socket.on("new_event_invite", function (data) {
    $("#regular_notification_bell").hide()
    $("#new_notification_bell").show()
    localStorage.setItem("newNotification", true);
    createNotification(APP_NAME, data.username + " has invited you to join their event");
  });

  private_socket.on("event_invite_approve", function (data) {
    $("#regular_notification_bell").hide()
    $("#new_notification_bell").show()
    localStorage.setItem("newNotification", true);
    createNotification(APP_NAME, data.username + " has accepted your event invitation");
  });

  private_socket.on("new_event_join", function (data) {
    $("#regular_notification_bell").hide()
    $("#new_notification_bell").show()
    localStorage.setItem("newNotification", true);
    createNotification(APP_NAME, data.username + " has joined your event");
  });

});



