///document.getElementById("myButton").addEventListener("click", fetchData);

$(function(){

	$('#myButton').click(function(){
		console.log("button 1");

		(async () => {
			const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
			let result;
			try {
			  [{result}] = await chrome.scripting.executeScript({
				target: {tabId: tab.id},
				func: () => document.body.innerHTML,
			  });
			} catch (e) {
			  document.body.textContent = 'Cannot access page';
			  return;
			}

			console.log(result.slice(0,100) + "..."); // only show a snippet for now
			
		  })();
		
		///const res=await fetch ("https://api.coronavirus.data.gov.uk/v1/data");
		///const record=await res.json();
	
		var serverhost = 'http://127.0.0.1:8000/';
		
		fetch(serverhost)
		.then(response => response.json())
		//.then(response => sendResponse({farewell: response}))   // ReferenceError: sendResponse is not defined
		.catch(error => console.log(error))


		/*chrome.runtime.onMessage.addListener(
		function(request, sender, sendResponse) {
				var url = serverhost +  '/get/' ;
				return true;  // Will respond asynchronously.
		});*/
		
	});


	$('#myButton2').click(function(){
		console.log("button 2");

        let formData = new FormData();


		let page_url = "";

		chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
			let activeTab = tabs[0];
			console.log(activeTab.url);
			page_url = activeTab.url;

			formData.append('page_url', page_url);
			formData.append('tag', "whatever");

			let posting = $.ajax({
				type: "POST",
				enctype: 'multipart/form-data',
				url: "http://127.0.0.1:8000/send_url/",
				data: formData,
				processData: false,
				contentType: false,
				// cache: false,
				timeout: 800000,
				beforeSend: function(){console.log("sending"); return"sending";},

				// "data" is the json response from backend
				success: function(data){console.log("success"); console.log(data); showDownloadLinks(data); return "success";},
				error: function(){console.log("error"); return"error";},
			});


			function showDownloadLinks(data){
				let download_links_ = data.download_links;
				console.log(download_links_);

				// Table for download links

				let table = document.createElement('table');
				let header = document.createElement('thead');
				let tr_ = document.createElement('tr');
				let th_ = document.createElement('th');
				th_.textContent = "Table Links";
				tr_.appendChild(th_);
				header.appendChild(tr_);
				table.appendChild(header);
				let tbody_ = document.createElement('tbody');

				if (download_links_.length > 0){

					for (let i = 0; i < download_links_.length; i++) {
						let row = document.createElement('tr');
						let cell = document.createElement('td');

						let a = document.createElement('a');
						let linkText = document.createTextNode("Table: " + i );
						a.appendChild(linkText);
						a.title = "Download Table: " + i;
						a.href = download_links_[i];
						let download_button = document.createElement('i');
						download_button.className = "fa fa-download download_button"
						a.appendChild(download_button)

						cell.appendChild(a);
						row.appendChild(cell);
						tbody_.appendChild(row);
					}
				}

				else{
					let row = document.createElement('tr');
					let emptiness = document.createElement('td');
					emptiness.textContent = "No Table Found on this website.";
					tbody_.appendChild(emptiness)
				}

				table.appendChild(tbody_);
				document.getElementById('download_links_table').innerHTML = table.innerHTML;
			}


		}); // since this is async, everything that depends on it has to stay inside.



	});

});








