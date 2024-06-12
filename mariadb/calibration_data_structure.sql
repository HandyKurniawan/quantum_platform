CREATE DATABASE  IF NOT EXISTS `framework` /*!40100 DEFAULT CHARACTER SET latin1 COLLATE latin1_swedish_ci */;
USE `framework`;
-- MySQL dump 10.13  Distrib 8.0.34, for Linux (x86_64)
--
-- Host: ec2-13-60-50-75.eu-north-1.compute.amazonaws.com    Database: calibration_data
-- ------------------------------------------------------
-- Server version	5.5.5-10.5.20-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `hardware`
--

DROP TABLE IF EXISTS `hardware`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `hardware` (
  `hw_name` varchar(25) NOT NULL,
  `hw_provider` varchar(45) NOT NULL,
  `number_of_qubit` int(11) NOT NULL,
  `hw_description` varchar(100) NOT NULL,
  `2q_native_gates` varchar(45) DEFAULT NULL,
  `status` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`hw_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ibm`
--

DROP TABLE IF EXISTS `ibm`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ibm` (
  `calibration_id` int(11) NOT NULL AUTO_INCREMENT,
  `calibration_datetime` datetime NOT NULL,
  `hw_name` varchar(25) NOT NULL,
  `data_source` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`calibration_id`),
  KEY `fk_ibm_1_idx` (`hw_name`),
  KEY `idx_hw_name` (`hw_name`),
  KEY `idx_ibm_hw_calibration` (`calibration_id`,`hw_name`),
  KEY `idx_ibm_calibration_hw` (`calibration_id`,`hw_name`,`calibration_datetime`),
  CONSTRAINT `fk_ibm_1` FOREIGN KEY (`hw_name`) REFERENCES `hardware` (`hw_name`)
) ENGINE=InnoDB AUTO_INCREMENT=36535 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ibm_gate_spec`
--

DROP TABLE IF EXISTS `ibm_gate_spec`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ibm_gate_spec` (
  `calibration_id` int(11) NOT NULL,
  `qubit_control` int(11) NOT NULL,
  `qubit_target` int(11) NOT NULL,
  `gate_name` varchar(45) NOT NULL,
  `date` datetime DEFAULT NULL,
  `gate_error` decimal(35,28) DEFAULT NULL,
  `gate_length` decimal(35,28) DEFAULT NULL,
  PRIMARY KEY (`calibration_id`,`qubit_control`,`qubit_target`,`gate_name`),
  KEY `idx_cal_id_qubit` (`calibration_id`,`qubit_control`),
  KEY `idx_calibration_id` (`calibration_id`),
  KEY `idx_qubit_control_target` (`qubit_control`,`qubit_target`),
  KEY `idx_ibm_hw_calibration_qubit` (`calibration_id`,`qubit_control`),
  KEY `idx_ibm_hw_calibration_qubits` (`calibration_id`,`qubit_control`,`qubit_target`,`gate_name`,`date`,`gate_error`,`gate_length`),
  CONSTRAINT `ibm_gate_spec_calibration_id` FOREIGN KEY (`calibration_id`) REFERENCES `ibm` (`calibration_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary view structure for view `ibm_one_qubit_gate_spec`
--

DROP TABLE IF EXISTS `ibm_one_qubit_gate_spec`;
/*!50001 DROP VIEW IF EXISTS `ibm_one_qubit_gate_spec`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `ibm_one_qubit_gate_spec` AS SELECT 
 1 AS `hw_name`,
 1 AS `calibration_id`,
 1 AS `qubit`,
 1 AS `id_date`,
 1 AS `reset_date`,
 1 AS `sx_date`,
 1 AS `x_date`,
 1 AS `id_error`,
 1 AS `reset_error`,
 1 AS `sx_error`,
 1 AS `x_error`,
 1 AS `id_length`,
 1 AS `reset_length`,
 1 AS `sx_length`,
 1 AS `x_length`*/;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `ibm_qubit_spec`
--

DROP TABLE IF EXISTS `ibm_qubit_spec`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ibm_qubit_spec` (
  `calibration_id` int(11) NOT NULL,
  `qubit` int(11) NOT NULL,
  `T1` decimal(35,28) DEFAULT NULL,
  `T2` decimal(35,28) DEFAULT NULL,
  `frequency` decimal(35,28) DEFAULT NULL,
  `anharmonicity` decimal(35,28) DEFAULT NULL,
  `readout_error` decimal(35,28) DEFAULT NULL,
  `prob_meas0_prep1` decimal(35,28) DEFAULT NULL,
  `prob_meas1_prep0` decimal(35,28) DEFAULT NULL,
  `readout_length` decimal(35,28) DEFAULT NULL,
  `T1_date` datetime DEFAULT NULL,
  `T2_date` datetime DEFAULT NULL,
  `frequency_date` datetime DEFAULT NULL,
  `anharmonicity_date` datetime DEFAULT NULL,
  `readout_error_date` datetime DEFAULT NULL,
  `prob_meas0_prep1_date` datetime DEFAULT NULL,
  `prob_meas1_prep0_date` datetime DEFAULT NULL,
  `readout_length_date` datetime DEFAULT NULL,
  PRIMARY KEY (`calibration_id`,`qubit`),
  CONSTRAINT `ibm_qubit_spec_calibration_id` FOREIGN KEY (`calibration_id`) REFERENCES `ibm` (`calibration_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary view structure for view `ibm_two_qubit_gate_spec`
--

DROP TABLE IF EXISTS `ibm_two_qubit_gate_spec`;
/*!50001 DROP VIEW IF EXISTS `ibm_two_qubit_gate_spec`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `ibm_two_qubit_gate_spec` AS SELECT 
 1 AS `hw_name`,
 1 AS `calibration_datetime`,
 1 AS `calibration_id`,
 1 AS `qubit_control`,
 1 AS `qubit_target`,
 1 AS `cx_date`,
 1 AS `cz_date`,
 1 AS `ecr_date`,
 1 AS `cx_error`,
 1 AS `cz_error`,
 1 AS `ecr_error`,
 1 AS `cx_length`,
 1 AS `cz_length`,
 1 AS `ecr_length`*/;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `rigetti`
--

DROP TABLE IF EXISTS `rigetti`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rigetti` (
  `calibration_id` int(11) NOT NULL AUTO_INCREMENT,
  `calibration_datetime` datetime NOT NULL,
  `hw_name` varchar(25) NOT NULL,
  PRIMARY KEY (`calibration_id`),
  KEY `hw_name_idx` (`hw_name`),
  CONSTRAINT `hw_name` FOREIGN KEY (`hw_name`) REFERENCES `hardware` (`hw_name`)
) ENGINE=InnoDB AUTO_INCREMENT=2887 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rigetti_edge_spec`
--

DROP TABLE IF EXISTS `rigetti_edge_spec`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rigetti_edge_spec` (
  `calibration_id` int(11) NOT NULL,
  `qubit_from` int(11) NOT NULL,
  `qubit_to` int(11) NOT NULL,
  `fCZ` decimal(35,28) DEFAULT NULL,
  `fCZ_std_err` decimal(35,28) DEFAULT NULL,
  `fCPHASE` decimal(35,28) DEFAULT NULL,
  `fCPHASE_std_err` decimal(35,28) DEFAULT NULL,
  `fXY` decimal(35,28) DEFAULT NULL,
  `fXY_std_err` decimal(35,28) DEFAULT NULL,
  PRIMARY KEY (`calibration_id`,`qubit_from`,`qubit_to`),
  CONSTRAINT `calibration_two_qubit_id` FOREIGN KEY (`calibration_id`) REFERENCES `rigetti` (`calibration_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rigetti_qubit_spec`
--

DROP TABLE IF EXISTS `rigetti_qubit_spec`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rigetti_qubit_spec` (
  `calibration_id` int(11) NOT NULL,
  `qubit` int(11) NOT NULL,
  `T1` decimal(35,28) DEFAULT NULL,
  `T2` decimal(35,28) DEFAULT NULL,
  `fActiveReset` decimal(35,28) DEFAULT NULL,
  `fRO` decimal(35,28) DEFAULT NULL,
  `f1QRB` decimal(35,28) DEFAULT NULL,
  `f1QRB_std_err` decimal(35,28) DEFAULT NULL,
  `f1Q_Simultaneous_RB` decimal(35,28) DEFAULT NULL,
  `f1Q_Simultaneous_RB_std_err` decimal(35,28) DEFAULT NULL,
  PRIMARY KEY (`calibration_id`,`qubit`),
  CONSTRAINT `calibration_single_qubit_id` FOREIGN KEY (`calibration_id`) REFERENCES `rigetti` (`calibration_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping events for database 'calibration_data'
--

--
-- Dumping routines for database 'calibration_data'
--

--
-- Final view structure for view `ibm_one_qubit_gate_spec`
--

/*!50001 DROP VIEW IF EXISTS `ibm_one_qubit_gate_spec`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`handy`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `ibm_one_qubit_gate_spec` AS select `i`.`hw_name` AS `hw_name`,`g`.`calibration_id` AS `calibration_id`,`g`.`qubit_control` AS `qubit`,max(case when `g`.`gate_name` = 'id' then `g`.`date` else 0 end) AS `id_date`,max(case when `g`.`gate_name` = 'reset' then `g`.`date` else 0 end) AS `reset_date`,max(case when `g`.`gate_name` = 'sx' then `g`.`date` else 0 end) AS `sx_date`,max(case when `g`.`gate_name` = 'x' then `g`.`date` else 0 end) AS `x_date`,sum(case when `g`.`gate_name` = 'id' then `g`.`gate_error` else 0 end) AS `id_error`,sum(case when `g`.`gate_name` = 'reset' then `g`.`gate_error` else 0 end) AS `reset_error`,sum(case when `g`.`gate_name` = 'sx' then `g`.`gate_error` else 0 end) AS `sx_error`,sum(case when `g`.`gate_name` = 'x' then `g`.`gate_error` else 0 end) AS `x_error`,sum(case when `g`.`gate_name` = 'id' then `g`.`gate_length` else 0 end) AS `id_length`,sum(case when `g`.`gate_name` = 'reset' then `g`.`gate_length` else 0 end) AS `reset_length`,sum(case when `g`.`gate_name` = 'sx' then `g`.`gate_length` else 0 end) AS `sx_length`,sum(case when `g`.`gate_name` = 'x' then `g`.`gate_length` else 0 end) AS `x_length` from (`ibm_gate_spec` `g` join `ibm` `i` on(`g`.`calibration_id` = `i`.`calibration_id`)) group by `i`.`hw_name`,`g`.`calibration_id`,`g`.`qubit_control` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `ibm_two_qubit_gate_spec`
--

/*!50001 DROP VIEW IF EXISTS `ibm_two_qubit_gate_spec`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`handy`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `ibm_two_qubit_gate_spec` AS select `i`.`hw_name` AS `hw_name`,`i`.`calibration_datetime` AS `calibration_datetime`,`g`.`calibration_id` AS `calibration_id`,`g`.`qubit_control` AS `qubit_control`,`g`.`qubit_target` AS `qubit_target`,max(case when `g`.`gate_name` = 'cx' then `g`.`date` else 0 end) AS `cx_date`,max(case when `g`.`gate_name` = 'cz' then `g`.`date` else 0 end) AS `cz_date`,max(case when `g`.`gate_name` = 'ecr' then `g`.`date` else 0 end) AS `ecr_date`,sum(case when `g`.`gate_name` = 'cx' then `g`.`gate_error` else 0 end) AS `cx_error`,sum(case when `g`.`gate_name` = 'cz' then `g`.`gate_error` else 0 end) AS `cz_error`,sum(case when `g`.`gate_name` = 'ecr' then `g`.`gate_error` else 0 end) AS `ecr_error`,sum(case when `g`.`gate_name` = 'cx' then `g`.`gate_length` else 0 end) AS `cx_length`,sum(case when `g`.`gate_name` = 'cz' then `g`.`gate_length` else 0 end) AS `cz_length`,sum(case when `g`.`gate_name` = 'ecr' then `g`.`gate_length` else 0 end) AS `ecr_length` from (`ibm_gate_spec` `g` join `ibm` `i` on(`g`.`calibration_id` = `i`.`calibration_id`)) where `g`.`qubit_control` <> `g`.`qubit_target` group by `i`.`hw_name`,`g`.`calibration_id`,`g`.`qubit_control`,`g`.`qubit_target` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-06-11 10:55:52
