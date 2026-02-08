# Code Citations

## License: unknown — EventGenre.js

Link: <https://github.com/JokaMilen/meet/blob/68cd53f260ddfa926e087649d624d940f52feaf6/src/EventGenre.js>

```jsx
%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%" // Center X-coordinate of the pie chart
            cy="50%" // Center Y-coordinate of the pie chart
            labelLine={false}
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    <
```


## License: unknown — CustomBarChart.jsx

Link: <https://github.com/prabhathkumar1729/expensetracker-react/blob/cf2cfdee1b2a0caa28fc096f99bd38bffbb2e7c5/src/components/CustomBarChart.jsx>

```jsx

%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    <
```


## License: unknown — Data.jsx

Link: <https://github.com/ss-sahoo/user-wallet/blob/c99df87dcd3d741cd91a507d1bd0f1cc395c2f20/src/pages/data/Data.jsx>
