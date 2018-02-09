# Laboratory Exercise 2 - Python OOP

For this exercise, you will test your skills on the basic OOP constructs in Python to write the solution of the problem described below.

## Submission

Once you are done, submit your code as a post (i.e., inline) in Piazza. You must submit your code at the end of the lab session to get full points from this exercise. 


### Problem 1 Banking in Python

Write a class called `SavingsAccount` that has the following properties and behaviours (Note that the (-,+) before an identifier denotes the visibility of the property or method):

- Properties 
  - `+balance`, denotes the remaining balance of a bank account object.
  - `+interest`, denotes the interest rate associated to a bank account object.
- Behaviours
  - `+deposit(amount)`, returns the new balance.
  - `+withdraw(amount)`, returns the new balance.
  - `+add_interest()`, computes the new balance using the following formula `balance = balance + compute_interest()` where `compute_interest` is a private method that computes and returns the interest using the formula `interest = balance * interest`.
  - `+bank_information()`, a static method that displays the name and other arbitrary information about the bank to which the account is registered. For this exercise, this method should just return the string `Banko ni Juan` when called.  

- Constructors. The class should respond to the following calls to its constructor method.
  - `SavingsAccount()`, no argument call to the constructor should set the default value of `balance` to 0 and 0.05 for the `interest`.
  - `SavingsAccount(number)`, a call to the constructor with only one parameter should set the value of `balance = number1` and `interest = 0.05`. 
  - `SavingsAccount(number1, number2)`, a call to the constructor with both parameters set should set the value of `balance = number1` and `interest = number2`.
  
 ### Example Test Cases
 
 ```
 > a = SavingsAccount()
 >
 > a.balance  # should return 0
 >
 > a.interest # should return 0.05
 > a.deposit(100) # should return 100
 >
 > SavingsAccount.bank_information()  # should return "Banko ni Juan"
 ```
