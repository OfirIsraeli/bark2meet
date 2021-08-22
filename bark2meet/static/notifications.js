const ICON = "/static/logo-medium.png";

const askForPermission = () => {
  Notification.requestPermission().then((permission) => {});
};

const showNotification = (title, msg) => {
  const notification = new Notification(title, { body: msg, icon: ICON });
};

const createNotification = (body = "", msg = "") => {
  switch (Notification.permission) {
    case "granted":
      showNotification(body, msg);
    case "default":
      askForPermission();
    case "denied":
      return;
  }
};

$(document).ready(function () {
  var private_socket = io("/private");

  // $("#create-notification").on("click", function () {
  //   createNotification("title", "body");
  // });

  // $("#new-walk").on("click", function () {
  //   private_socket.emit("friend-walk");
  // });

  $("#realtime_porter").on("port_friend_request", function (event, data) {
    private_socket.emit("friend-request-notification", data);
  });

  $("#realtime_porter").on("port_friend_approve", function (event, data) {
    private_socket.emit("friend-approve-notification", data);
  });

  $("#realtime_porter").on("port_event_invite", function (event, data) {
    private_socket.emit("event-invite-notification", data);
  });

  $("#realtime_porter").on("port_event_approve", function (event, data) {
    private_socket.emit("event-approve-notification", data);
  });

  $("#realtime_porter").on("port_event_join", function (event, data) {
    private_socket.emit("event-join-notification", data);
  });
  
});
