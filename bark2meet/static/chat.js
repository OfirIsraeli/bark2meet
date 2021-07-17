const space = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;";
$(document).ready(function () {
  var socket = io.connect("/");

  var socket_messages = io("/messages");

  socket.on("new_friend_walk", function (data) {
    console.log("im here")
  });

  socket_messages.on("from flask", function (msg) {
    alert(msg);
  });

  socket.on("server orginated", function (msg) {
    alert(msg);
  });

  var private_socket = io("/private");
  private_socket.emit("email");

  $("#show_notifications").on("click", function () {
    $(this).next().show();
  });

  $('[id^="chat_with_"]').on("click", function () {
    var recipient = $(this).attr("id").slice(10);
    var recipientUsername = $(this).text().slice(10);

    $(this).next().show();
    fetch("/api/history/" + recipient)
      .then(function (response) {
        return response.json();
      })
      .then(function (text) {
        let history = text.chat;
        history.forEach((entry) => {
          if (entry.sender === recipient) {
            $('[id="' + recipient + '"]').append(
              "<li>" +
                recipientUsername +
                ":\t" +
                entry.msg +
                space.repeat(10) +
                entry.send_time +
                "</li>"
            );
          } else {
            $('[id="' + recipient + '"]').append(
              "<li>" + "Me:\t" + entry.msg + space.repeat(10) + entry.send_time + "</li>"
            );
          }
        });
      });
  });

  $('[id^="button_"]').on("click", function () {
    var recipientUsername = $(this).text().slice(8);
    var recipient = $(this).attr("id").slice(7);
    var message_to_send = $('[id="input_text_' + recipient + '"]').val();
    private_socket.emit("private_message", { email: recipient, message: message_to_send });
    $('[id="input_text_' + recipient + '"]').val("");
    $('[id="' + recipient + '"]').append(
      "<li>" + "Me" + ":\t" + message_to_send + space.repeat(10) + new Date() + "</li>"
    );

    // $("#input_text_" + recipient).val("");
    // $("#" + recipient).append(
    //   "<li>" + "Me" + ":\t" + message_to_send + space.repeat(10) + new Date() + "</li>"
    // );
  });

  private_socket.on("new_private_message", function (data) {
    $('[id="' + data.email + '"]').append(
      "<li>" + data.username + ":\t" + data.msg + space.repeat(10) + data.send_time + "</li>"
    );
  });
  /*
  private_socket.on("new_private_history", function (data) {
    history = data["history"];
    console.log("hi", data["history"], history);
    history.forEach((entry) => {
      $("#" + data.username).append("<li>" + entry.sender + ":\t" + entry.msg + "</li>");
    });
  });*/

  private_socket.on("invalid_user", function (msg) {
    alert(msg);
  });

  // ------------------------------- FRIENDS WALK EVENTS -------------------------------
  private_socket.on("new_friend_walk", function (data) {
    console.log("im here")
    createNotification(data.username + " is on the go!", "");
    // $("#notifications_list").prepend(
    //   "<li class='new_notifications'>" +
    //     data.username +
    //     " is on the go! " +
    //     data.issue_time +
    //     "</li>"
    // );
  });
  // $('[id^="bababa"]').on("click", function () {
  //   console.log("helloss")
  // })
  // $('[id^="infoContentGreen"]').bind("DOMNodeInserted",function(){
  //   console.log("helloss")

  // })
  // ------------------------------- FRIENDS REQUEST EVENTS -------------------------------
  function acceptFriend(email){
    private_socket.emit("friend_request_approve", { email: email});
  }
  private_socket.on("new_friend_request", function (data) {
    const acceptButton = '<input type="checkbox" onClick="acceptFriend(data.email)" name="acceptFriendBtn" value="'+ userInfo.id +'" class="">'
    $('[id="' + "notifications_list" + '"]').append(
      "<li>" + data.username + ":\t" + data.msg + space.repeat(10) + data.send_time + acceptButton + "</li>"
    );
  });

});

/*
function getHistoryFileName(sender, recipient) {
  HOME_DIR = "chatHistory/";
  if (sender < recipient) {
    return HOME_DIR + sender + "&" + recipient + ".txt";
  }
  return HOME_DIR + recipient + "&" + sender + ".txt";
}

function writeMessageInHistory(sender, recipient, msg) {
  $.get(getHistoryFileName(sender, recipient))
    .done(function () {
      console.log("found");
    })
    .fail(function () {
      console.log("NOT found");
    });
}*/


