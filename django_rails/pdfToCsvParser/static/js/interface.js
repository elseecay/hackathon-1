$("#inputGroupFile01").change(function(e){
	$("#fileLabel").html(e.target.value.slice(e.target.value.lastIndexOf("\\") + 1));

	if (e.target.value.slice(e.target.value.lastIndexOf("\\") + 1).length) {
		$('#submitFileButton').prop('disabled', false);
		$('#submitFileButton').removeClass('btn-outline-primary');
		$('#submitFileButton').addClass('btn-primary');
		$('#submitFileButton').focus();
	}
	else {
		$('#submitFileButton').prop('disabled', true);
		$('#submitFileButton').removeClass('btn-primary');
		$('#submitFileButton').addClass('btn-outline-primary');
	}

});


$('#submitFileButton').click(function(){
	$('#submitFileButton').prop('disabled', true);

	let inp = document.getElementById('inputGroupFile01').files;

	if (inp.length) {		
		const formData = new FormData();
		console.log(inp[0]);

		let reader = new FileReader();
		reader.onloadend = () => {
			formData.append('file', reader.result);
			formData.append('csrfmiddlewaretoken', $("[name=csrfmiddlewaretoken]").val());

			fetch('/parser/send_pdf', {
				method: 'POST',
				body: formData,
				headers: {
					"X-CSRFToken": $("[name=csrfmiddlewaretoken]").val(),
					// 'Content-Type': 'multipart/form-data, application/x-www-form-urlencoded',
				},
			})
			.then(res => res.json())
			.then(res => renderResults(res))
			.catch(console.error);
		};
		
		reader.readAsDataURL(inp[0]);

	}
});

var results = null;

let renderResults = data => {

	results = data;

	renderPlot(data);

	document.getElementById('tbody').innerHTML = '';
	for (index in data) {
		row = data[index];
		console.log(row);
		let tr = document.createElement('tr');
		let td1 = document.createElement('td');
		td1.innerText = row['meter'];
		let td2 = document.createElement('td');
		td2.innerText = 'Уш';
		let td3 = document.createElement('td');
		td3.innerText = row['main_val'];
		let td4 = document.createElement('td');
		td4.innerText = row['val1'];
		let td5 = document.createElement('td');
		td5.innerText = row['val2'];
		let td6 = document.createElement('td');
		td6.innerText = row['val3'];
		tr.appendChild(td1);
		tr.appendChild(td2);
		tr.appendChild(td3);
		tr.appendChild(td4);
		tr.appendChild(td5);
		tr.appendChild(td6);
		document.getElementById('tbody').appendChild(tr);
	}
};

let renderPlot = data => {

	console.log(data);
	meters = data.map(v => v['meter']);
	meters2 = meters.map(v => v % 3380000);
	offsets = data.map(v => v['val1']);

	console.log(meters2);
	console.log(offsets);

	var trace1 = {
	  x: meters2,
	  y: offsets,
	  mode: 'lines',
	  name: 'Измерение',
	  line: {
	    dash: 'solid',
	    width: 4,
	    color: 'blue'
	  }
	};

	var trace2 = {
	  x: meters2,
	  y: new Array(meters.length).fill(1538),
	  mode: 'lines',
	  name: '3 степень отступления',
	  line: {
	    dash: 'dashdot',
	    width: 4,
	    color: 'orange',
	  }
	};

	var trace3 = {
	  x: meters2,
	  y: new Array(meters.length).fill(1510),
	  mode: 'lines',
	  name: 'Граница снизу',
	  line: {
	    dash: 'dot',
	    width: 4,
	 	color: 'red',
	  }
	};

	var trace4 = {
	  x: meters2,
	  y: new Array(meters.length).fill(1548),
	  mode: 'lines',
	  name: 'Граница сверху',
	  line: {
	    dash: 'dot',
	    width: 4,
	  	color: 'red',
	  }
	};

	var trace5 = {
	  x: meters2,
	  y: new Array(meters.length).fill(1520),
	  mode: 'lines',
	  name: '3 степень отступления',
	  line: {
	    dash: 'dot',
	    width: 4,
	    color: 'orange'
	  }
	};

	let datas = [trace1, trace2, trace3, trace4, trace5];

	var layout = {
	  title: 'График уширения колеи',
	  xaxis: {
	    range: [0, 1000],
	    autorange: false
	  },
	  yaxis: {
	    range: [1500, 1560],
	    autorange: false
	  },
	  legend: {
	    y: 0.5,
	    traceorder: 'reversed',
	    font: {
	      size: 16
	    }
	  }
	};

	Plotly.newPlot('plot', datas, layout);

}