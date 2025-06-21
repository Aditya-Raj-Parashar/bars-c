/*
TASKS


1. Insert a new record in your Orders table.

2. Add Primary key constraint for SalesmanId column in Salesman table. Add default
constraint for City column in Salesman table. Add Foreign key constraint for SalesmanId
column in Customer table. Add not null constraint in Customer_name column for the
Customer table.

3. Fetch the data where the Customer’s name is ending with ‘N’ also get the purchase
amount value greater than 500.

4. Using SET operators, retrieve the first result with unique SalesmanId values from two
tables, and the other result containing SalesmanId with duplicates from two tables.

5. Display the below columns which has the matching data.

Orderdate, Salesman Name, Customer Name, Commission, and City which has the
range of Purchase Amount between 500 to 1500.

6. Using right join fetch all the results from Salesman and Orders table.*/










-- SOLUTIONS




-- 1 new record
use master

select * from Orders
insert into orders (OrderId, CustomerId, SalesmanId, OrderDate, PurchaseAmount)
values (5004,1575,103,'12-12-2012',5000);

-- 2 add constraints

-- primary key

alter table salesman
add constraint prm_salesman primary key (salesmanID);

/*
error :

Msg 8111, Level 16, State 1, Line 10
Cannot define PRIMARY KEY constraint on nullable column in table 'salesman'.
Msg 1750, Level 16, State 0, Line 10
Could not create constraint or index. See previous errors.


 -> we are getting this error because according to given dataset salesmanID can be null
so we have to convert it into a not null column

*/

alter table Salesman
alter column SalesmanID int not null;
--now we can run the command
alter table Salesman
add constraint prm_salesman primary key (salesmanID);

-- Add default constraint

ALTER TABLE Salesman ADD CONSTRAINT def_city DEFAULT 'delhi' for City;


-- Add Foreign key constraint

ALTER TABLE Customer ADD CONSTRAINT fk_salesmanID 
FOREIGN KEY (SalesmanId) REFERENCES salesman(SalesmanId);

-- Add not null constraint
ALTER TABLE Customer ALTER COLUMN Customer_name VARCHAR(255) NOT NULL;



-- TASK 3: Fetch data where Customer's name ends with 'N' and purchase amount > 500


SELECT cs.Customer_name, ord.PurchaseAmount
FROM Customer cs
INNER JOIN Orders ord ON cs.CustomerId = ord.CustomerId
WHERE cs.Customer_name LIKE '%N' AND ord.PurchaseAmount > 500;

/* we dont have a single table with both name and salary thats why we are using 'joint' to join tables thus fulfilling the query
output :  we didnt get any output because there is no costumer name ending with N
*/

-- TASK 4: Using SET operators


-- First result: Unique SalesmanId values
SELECT SalesmanId FROM Salesman
UNION
SELECT SalesmanId FROM Customer;

/* output :
101
102
103
104
105
107
110
*/

-- Second result: SalesmanId with duplicates from both tables
SELECT SalesmanId FROM Salesman
UNION ALL
SELECT SalesmanId FROM Customer;


select * from Salesman,Orders,Customer

/* output :
101
102
103
104
105
101
103
104
107
110
*/

-- TASK 5: Display Orderdate, Salesman Name, Customer Name, Commission, City with Purchase Amount between 500 to 1500
SELECT 
    o.OrderDate ,
    s.Name 'Salesman Name',
    c.Customer_name 'Customer Name',
    s.Commission,
    c.City
FROM Orders o
JOIN Customer c ON o.CustomerId = c.CustomerId
JOIN Salesman s ON o.SalesmanId = s.SalesmanId
WHERE o.PurchaseAmount BETWEEN 500 AND 1500;

/* output  :- 

Orderdate	Salesman_Name	Customer_Name	Commission  	City
2021-07-01	Joe             	Andrew      	50.00	 California
*/

-- TASK 6: Using RIGHT JOIN to fetch all results from Salesman and Orders table
SELECT 
    s.SalesmanId,
    s.Name 'Salesman Name',
    s.Commission,
    s.City 'Salesman City',
    s.Age,
    o.OrderId,
    o.OrderDate,
    o.CustomerId,
    o.PurchaseAmount
FROM Orders o
RIGHT JOIN Salesman s ON o.SalesmanId = s.SalesmanId;

/* output : 
salesmanid   salesmanname    city     commition     orderid      orderdate       costumerid      amount
null            null         null       null          5053        2025-01-05         2334        2530.00
-- assingment end, sorry for any mistake and please revert it to @thedebugkid@gmail.com 😊