// This document is the extension pop-up itself. The console is extension's console.
// The Popup is reloaded everytime you open it.
// Popup code cannot work after popup is closed. But before that, you can send messages to other scripts to perform functions.

let server_host = "https://tablecatcher.azurewebsites.net/";

let table_for_scan_results = null
let table_header_while_waiting = null

let session_id = ""

$(function(){   // makes sure to start executing after popup's DOM is fully loaded.

	// Check if local server (localhost) is available; else, we will use Azure.
	let checking_local_connection = $.ajax({
		type: "GET",
		url: "http://127.0.0.1:8000/test_connection/",
		beforeSend: function(){
			function randomHexChar() {
				let hexList = ['1','2','3','4','5','6','7','8','9','0','a','b','c','d','e','f','g','h','k','m','n','o','p','r','s','t','y','z'];
				return hexList[Math.floor(Math.random() * hexList.length)];
			}
			session_id = randomHexChar() + randomHexChar() + randomHexChar() + randomHexChar();
		},
		success: function(json_response_from_backend){
			console.log("connected to localhost server");
			server_host = "http://127.0.0.1:8000/";
		},
		error: function(){
			console.log("not connected to localhost server")

			// Check if remote server (Azure) is available; else, we will fail.
			let checking_azure_connection = $.ajax({
				type: "GET",
				url: "https://tablecatcher.azurewebsites.net/test_connection/",
				success: function(json_response_from_backend){
					console.log("connected to Azure server");
					/* We used to set server_host = azure... in here, but this was creating a problem, which is:
						 If I try to load the extension in another page (B), and if server is not available for
						   test_connection yet (because it is not done processing the other (A) request, or whatever reason);
						 Then, B (this one) would try to connect to an empty string as a host.
						 
					   With new approach, request is sent, and the server may schedule it for later. But at least not error right away.
					*/
				},
				error: function(){
					console.log("not connected to Azure server either.")
				},
			});

		},
	});


	$('#scan_button_').click(function(){
		document.getElementById('download_links_table').innerHTML = "";

		chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {

			chrome.scripting.executeScript(
				{
				target: {tabId: tabs[0].id},

				// "function" works as if it is in content_script.js. "document" refers to the active tab page.
				function: function(){return document.getElementsByTagName('html')[0].innerHTML;}
				},
				(res) => {

					// send POST request to backend
					let data_to_send = JSON.stringify({ 'page_url': tabs[0].url, 'page_html': res[0].result, 'tag': 'whatever', 'session_id': session_id});
					let send_url = server_host + "scan_tables/";
					let posting = $.ajax({
						type: "POST",
						url: send_url,
						data: data_to_send,
						processData: false,
						datatype: "jsonp",
						contentType: 'application/json; charset=utf-8',
						beforeSend: function(){console.log("sending"); show_spinner_animation(); return"sending";},
						success: function(json_response_from_backend){
							console.log("success");
							createTable_for_DownloadLinks(json_response_from_backend.csv_download_links, json_response_from_backend.zip_download_link);
							embed_downloadLinks_on_tables_on_page(json_response_from_backend);
							return "success";
						},
						error: function(){
							table_for_scan_results.removeChild(table_header_while_waiting);
							document.getElementById('download_links_table').innerHTML = table_for_scan_results.innerHTML;
							console.log("error");
							toastr.error("Failed connect to Server or Not Responding."); return"error";
						},
					});

				}
			);


			function embed_downloadLinks_on_tables_on_page(downloadLinks_and_tableIndices){
				chrome.tabs.sendMessage(tabs[0].id, {data: downloadLinks_and_tableIndices, message:"sending_links"}, function(response) {
						console.log(' sent data to content_script.js ');
				});
			}

			function show_spinner_animation(){

				table_for_scan_results = document.createElement('table');

				table_header_while_waiting = document.createElement('thead');
				let tr_ = document.createElement('tr');
				let th_ = document.createElement('th');
				th_.textContent = "Scanning  ";

				let waiting_spinner = document.createElement('i');
				waiting_spinner.className = "fas fa-spinner fa-pulse"
				th_.appendChild(waiting_spinner)

				tr_.appendChild(th_);
				table_header_while_waiting.appendChild(tr_);
				table_for_scan_results.appendChild(table_header_while_waiting);

				document.getElementById('download_links_table').innerHTML = table_for_scan_results.innerHTML;
			}

			function createTable_for_DownloadLinks(csv_downloadLinks, zipDownloadLink){
				console.log(csv_downloadLinks);

				table_for_scan_results.removeChild(table_header_while_waiting)

				let header = document.createElement('thead');
				let tr_ = document.createElement('tr');
				let th_ = document.createElement('th');
				th_.textContent = "Scan Completed.";
				tr_.appendChild(th_);
				header.appendChild(tr_);
				table_for_scan_results.appendChild(header);

				let tbody_ = document.createElement('tbody');

				if (csv_downloadLinks.length > 0){

					let show_total = document.createElement('td');
					show_total.textContent = " " + csv_downloadLinks.length + " Tables Found.";
					tbody_.appendChild(show_total);

					/* "download all" button */

					let row = document.createElement('tr');
					let download_all = document.createElement('td');

					let link_and_icon = document.createElement('a');
					link_and_icon.href = zipDownloadLink;
					link_and_icon.target = "_blank";
					link_and_icon.style["text-decoration"] = "none";
					link_and_icon.style["color"] = "green";

					const text_inside= document.createTextNode(" Download All ");
					link_and_icon.appendChild(text_inside);

					let download_button = document.createElement('i');
					download_button.className = "fa fa-download download_button"
					link_and_icon.appendChild(download_button)

					download_all.appendChild(link_and_icon)
					row.appendChild(download_all)
					tbody_.appendChild(row);

					/* from Previous implementations, a list of download links
					// These links are already on the page now.
					for (let i = 0; i < downloadLinks.length; i++) {
						let row = document.createElement('tr');
						let cell = document.createElement('td');

						let a = document.createElement('a');
						let linkText = document.createTextNode("Table: " + (i+1) );
						a.appendChild(linkText);
						a.href = downloadLinks[i];
						let download_button = document.createElement('i');
						download_button.className = "fa fa-download download_button"
						a.appendChild(download_button)

						cell.appendChild(a);
						row.appendChild(cell);
						tbody_.appendChild(row);
					}
					*/
				}

				else{
					let emptiness = document.createElement('td');
					emptiness.textContent = "No Table Found on this Page.";
					tbody_.appendChild(emptiness);
				}

				table_for_scan_results.appendChild(tbody_);
				document.getElementById('download_links_table').innerHTML = table_for_scan_results.innerHTML;
			}


		}); // since this is async, everything that depends on it has to stay inside.


	});



	$('#screenshot_button_').click(function(){

		chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {

			chrome.tabs.sendMessage(tabs[0].id, {message: "take_screenshot", host_domain: server_host, session_id_: session_id}, function(response) {
				console.log('sent command to content_script.js');

				chrome.runtime.onMessage.addListener(function (request, sender, sendResponse) {
					if (request.message_me === true) {
						console.log(request.message_);
					}
				});
			});

		});


	});

});


/* JUST FOR TESTING SOME STUFF.

document.addEventListener('DOMContentLoaded', () => {

    // for resetting some stuff when it will be closed. Controlled by background script.
    // chrome.runtime.connect({ name: "popup_opened" });

    const startButton = document.getElementById('captureButton');
    startButton.addEventListener('click', () => {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            chrome.tabs.sendMessage(tabs[0].id, { command: 'startHighlighting' });
        });
    });

    // DOES NOT WORK.
    intention was: Prevent the shift of focus from the popup to the page (when clicked on page.) Thus prevent the popup from closing.
    setTimeout(function() {
        document.body.focus();
    }, 0);

});

 */