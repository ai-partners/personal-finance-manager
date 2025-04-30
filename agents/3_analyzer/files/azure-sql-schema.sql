-- Database schema for financial management system - Azure SQL compatible

-- Users table
CREATE TABLE Users (
    Id INT PRIMARY KEY IDENTITY(1,1),
    Name NVARCHAR(100) NOT NULL,
    Email NVARCHAR(100) NOT NULL UNIQUE
);

-- Categories table
CREATE TABLE Categories (
    Id INT PRIMARY KEY IDENTITY(1,1),
    Name NVARCHAR(100) NOT NULL,
    Description NVARCHAR(1000),
    Type NVARCHAR(50),
    UserId INT NOT NULL,
    CONSTRAINT FK_Categories_Users FOREIGN KEY (UserId) REFERENCES Users(Id)
);

-- Accounts table
CREATE TABLE Accounts (
    Id INT PRIMARY KEY IDENTITY(1,1),
    Name NVARCHAR(100) NOT NULL,
    Description NVARCHAR(1000),
    Type NVARCHAR(50),
    UserId INT NOT NULL,
    CONSTRAINT FK_Accounts_Users FOREIGN KEY (UserId) REFERENCES Users(Id)
);

-- Transactions table
CREATE TABLE Transactions (
    Id INT PRIMARY KEY IDENTITY(1,1),
    Type NVARCHAR(50) NOT NULL,
    AccountId INT NOT NULL,
    CategoryId INT NOT NULL,
    UserId INT NOT NULL,
    Date DATETIME2 NOT NULL,
    Amount DECIMAL(10, 2) NOT NULL,
    Description NVARCHAR(1000),
    AttachmentUrl NVARCHAR(255),
    CONSTRAINT FK_Transactions_Accounts FOREIGN KEY (AccountId) REFERENCES Accounts(Id),
    CONSTRAINT FK_Transactions_Categories FOREIGN KEY (CategoryId) REFERENCES Categories(Id),
    CONSTRAINT FK_Transactions_Users FOREIGN KEY (UserId) REFERENCES Users(Id)
);

-- Budget table
CREATE TABLE Budget (
    Id INT PRIMARY KEY IDENTITY(1,1),
    CategoryId INT NOT NULL,
    Year INT NOT NULL,
    Month INT NOT NULL,
    Amount DECIMAL(10, 2) NOT NULL,
    UserId INT NOT NULL,
    CONSTRAINT FK_Budget_Categories FOREIGN KEY (CategoryId) REFERENCES Categories(Id),
    CONSTRAINT FK_Budget_Users FOREIGN KEY (UserId) REFERENCES Users(Id),
    CONSTRAINT UQ_Budget UNIQUE (CategoryId, Year, Month, UserId)
);